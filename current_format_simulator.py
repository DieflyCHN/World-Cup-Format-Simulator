"""
Monte Carlo simulator for the 48-team, 12-group World Cup format.

The script has three user-facing inputs: number of simulations, number of worker
threads, and an optional random seed. Each simulation performs:
random draw -> 12 four-team groups -> best third-place selection -> fixed
32-team bracket -> aggregate odds.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import math
import os
import random

# Elo logistic scale used for winner-takes-all matches.
KNOCKOUT_K = 800

# Per-match form noise. It prevents knockout outcomes from being purely
# deterministic by rating while keeping stronger teams favored.
KNOCKOUT_FORM_SIGMA = 120

GROUP_WIN_POINTS = 3
GROUP_DRAW_POINTS = 1
GROUP_SIZE = 4
GROUP_NAMES = tuple("ABCDEFGHIJKL")
THIRD_PLACE_QUALIFIERS = 8


@dataclass(frozen=True)
class Team:
    code: str
    name: str
    rating: int


@dataclass
class TeamStats:
    qualified: int = 0
    round_of_16: int = 0
    quarterfinal: int = 0
    semifinal: int = 0
    final: int = 0
    champion: int = 0


@dataclass(frozen=True)
class SimulationResult:
    qualified: list[str]
    round_of_16: list[str]
    quarterfinal: list[str]
    semifinal: list[str]
    final: list[str]
    champion: str


@dataclass(frozen=True)
class KnockoutResult:
    round_of_16: list[str]
    quarterfinal: list[str]
    semifinal: list[str]
    final: list[str]
    champion: str


@dataclass(frozen=True)
class GroupStageResult:
    qualified: list[str]
    qualifiers_by_slot: dict[str, str]
    best_third_place_slots: list[str]


@dataclass
class GroupStanding:
    code: str
    points: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    tie_breaker: float = 0.0

    @property
    def goal_diff(self):
        return self.goals_for - self.goals_against


# FIFA's third-place assignment table for a 12-group, 8-best-third format.
# Each key is the set of third-place groups that qualified; each value maps the
# target winner slots A1, B1, D1, E1, G1, I1, K1, L1 to their third-place opponent.
THIRD_PLACE_TARGET_WINNER_SLOTS = ("A1", "B1", "D1", "E1", "G1", "I1", "K1", "L1")

# Compressed FIFA third-place assignment table. Each entry is
# "<advanced third-place group letters>:<opponents for A1,B1,D1,E1,G1,I1,K1,L1>".
THIRD_PLACE_ASSIGNMENT_DATA = (
    "EFGHIJKL:EJIFHGLK;DFGHIJKL:HGIDJFLK;DEGHIJKL:EJIDHGLK;DEFHIJKL:EJIDHFLK;DEFGIJKL:EGIDJFLK;DEFGHJKL:EGJDHFLK;DEFGHIKL:EGIDHFLK;DEFGHIJL:EGJDHFLI;"
    "DEFGHIJK:EGJDHFIK;CFGHIJKL:HGICJFLK;CEGHIJKL:EJICHGLK;CEFHIJKL:EJICHFLK;CEFGIJKL:EGICJFLK;CEFGHJKL:EGJCHFLK;CEFGHIKL:EGICHFLK;CEFGHIJL:EGJCHFLI;"
    "CEFGHIJK:EGJCHFIK;CDGHIJKL:HGICJDLK;CDFHIJKL:CJIDHFLK;CDFGIJKL:CGIDJFLK;CDFGHJKL:CGJDHFLK;CDFGHIKL:CGIDHFLK;CDFGHIJL:CGJDHFLI;CDFGHIJK:CGJDHFIK;"
    "CDEHIJKL:EJICHDLK;CDEGIJKL:EGICJDLK;CDEGHJKL:EGJCHDLK;CDEGHIKL:EGICHDLK;CDEGHIJL:EGJCHDLI;CDEGHIJK:EGJCHDIK;CDEFIJKL:CJEDIFLK;CDEFHJKL:CJEDHFLK;"
    "CDEFHIKL:CEIDHFLK;CDEFHIJL:CJEDHFLI;CDEFHIJK:CJEDHFIK;CDEFGJKL:CGEDJFLK;CDEFGIKL:CGEDIFLK;CDEFGIJL:CGEDJFLI;CDEFGIJK:CGEDJFIK;CDEFGHKL:CGEDHFLK;"
    "CDEFGHJL:CGJDHFLE;CDEFGHJK:CGJDHFEK;CDEFGHIL:CGEDHFLI;CDEFGHIK:CGEDHFIK;CDEFGHIJ:CGJDHFEI;BFGHIJKL:HJBFIGLK;BEGHIJKL:EJIBHGLK;BEFHIJKL:EJBFIHLK;"
    "BEFGIJKL:EJBFIGLK;BEFGHJKL:EJBFHGLK;BEFGHIKL:EGBFIHLK;BEFGHIJL:EJBFHGLI;BEFGHIJK:EJBFHGIK;BDGHIJKL:HJBDIGLK;BDFHIJKL:HJBDIFLK;BDFGIJKL:IGBDJFLK;"
    "BDFGHJKL:HGBDJFLK;BDFGHIKL:HGBDIFLK;BDFGHIJL:HGBDJFLI;BDFGHIJK:HGBDJFIK;BDEHIJKL:EJBDIHLK;BDEGIJKL:EJBDIGLK;BDEGHJKL:EJBDHGLK;BDEGHIKL:EGBDIHLK;"
    "BDEGHIJL:EJBDHGLI;BDEGHIJK:EJBDHGIK;BDEFIJKL:EJBDIFLK;BDEFHJKL:EJBDHFLK;BDEFHIKL:EIBDHFLK;BDEFHIJL:EJBDHFLI;BDEFHIJK:EJBDHFIK;BDEFGJKL:EGBDJFLK;"
    "BDEFGIKL:EGBDIFLK;BDEFGIJL:EGBDJFLI;BDEFGIJK:EGBDJFIK;BDEFGHKL:EGBDHFLK;BDEFGHJL:HGBDJFLE;BDEFGHJK:HGBDJFEK;BDEFGHIL:EGBDHFLI;BDEFGHIK:EGBDHFIK;"
    "BDEFGHIJ:HGBDJFEI;BCGHIJKL:HJBCIGLK;BCFHIJKL:HJBCIFLK;BCFGIJKL:IGBCJFLK;BCFGHJKL:HGBCJFLK;BCFGHIKL:HGBCIFLK;BCFGHIJL:HGBCJFLI;BCFGHIJK:HGBCJFIK;"
    "BCEHIJKL:EJBCIHLK;BCEGIJKL:EJBCIGLK;BCEGHJKL:EJBCHGLK;BCEGHIKL:EGBCIHLK;BCEGHIJL:EJBCHGLI;BCEGHIJK:EJBCHGIK;BCEFIJKL:EJBCIFLK;BCEFHJKL:EJBCHFLK;"
    "BCEFHIKL:EIBCHFLK;BCEFHIJL:EJBCHFLI;BCEFHIJK:EJBCHFIK;BCEFGJKL:EGBCJFLK;BCEFGIKL:EGBCIFLK;BCEFGIJL:EGBCJFLI;BCEFGIJK:EGBCJFIK;BCEFGHKL:EGBCHFLK;"
    "BCEFGHJL:HGBCJFLE;BCEFGHJK:HGBCJFEK;BCEFGHIL:EGBCHFLI;BCEFGHIK:EGBCHFIK;BCEFGHIJ:HGBCJFEI;BCDHIJKL:HJBCIDLK;BCDGIJKL:IGBCJDLK;BCDGHJKL:HGBCJDLK;"
    "BCDGHIKL:HGBCIDLK;BCDGHIJL:HGBCJDLI;BCDGHIJK:HGBCJDIK;BCDFIJKL:CJBDIFLK;BCDFHJKL:CJBDHFLK;BCDFHIKL:CIBDHFLK;BCDFHIJL:CJBDHFLI;BCDFHIJK:CJBDHFIK;"
    "BCDFGJKL:CGBDJFLK;BCDFGIKL:CGBDIFLK;BCDFGIJL:CGBDJFLI;BCDFGIJK:CGBDJFIK;BCDFGHKL:CGBDHFLK;BCDFGHJL:CGBDHFLJ;BCDFGHJK:HGBCJFDK;BCDFGHIL:CGBDHFLI;"
    "BCDFGHIK:CGBDHFIK;BCDFGHIJ:HGBCJFDI;BCDEIJKL:EJBCIDLK;BCDEHJKL:EJBCHDLK;BCDEHIKL:EIBCHDLK;BCDEHIJL:EJBCHDLI;BCDEHIJK:EJBCHDIK;BCDEGJKL:EGBCJDLK;"
    "BCDEGIKL:EGBCIDLK;BCDEGIJL:EGBCJDLI;BCDEGIJK:EGBCJDIK;BCDEGHKL:EGBCHDLK;BCDEGHJL:HGBCJDLE;BCDEGHJK:HGBCJDEK;BCDEGHIL:EGBCHDLI;BCDEGHIK:EGBCHDIK;"
    "BCDEGHIJ:HGBCJDEI;BCDEFJKL:CJBDEFLK;BCDEFIKL:CEBDIFLK;BCDEFIJL:CJBDEFLI;BCDEFIJK:CJBDEFIK;BCDEFHKL:CEBDHFLK;BCDEFHJL:CJBDHFLE;BCDEFHJK:CJBDHFEK;"
    "BCDEFHIL:CEBDHFLI;BCDEFHIK:CEBDHFIK;BCDEFHIJ:CJBDHFEI;BCDEFGKL:CGBDEFLK;BCDEFGJL:CGBDJFLE;BCDEFGJK:CGBDJFEK;BCDEFGIL:CGBDEFLI;BCDEFGIK:CGBDEFIK;"
    "BCDEFGIJ:CGBDJFEI;BCDEFGHL:CGBDHFLE;BCDEFGHK:CGBDHFEK;BCDEFGHJ:HGBCJFDE;BCDEFGHI:CGBDHFEI;AFGHIJKL:HJIFAGLK;AEGHIJKL:EJIAHGLK;AEFHIJKL:EJIFAHLK;"
    "AEFGIJKL:EJIFAGLK;AEFGHJKL:EGJFAHLK;AEFGHIKL:EGIFAHLK;AEFGHIJL:EGJFAHLI;AEFGHIJK:EGJFAHIK;ADGHIJKL:HJIDAGLK;ADFHIJKL:HJIDAFLK;ADFGIJKL:IGJDAFLK;"
    "ADFGHJKL:HGJDAFLK;ADFGHIKL:HGIDAFLK;ADFGHIJL:HGJDAFLI;ADFGHIJK:HGJDAFIK;ADEHIJKL:EJIDAHLK;ADEGIJKL:EJIDAGLK;ADEGHJKL:EGJDAHLK;ADEGHIKL:EGIDAHLK;"
    "ADEGHIJL:EGJDAHLI;ADEGHIJK:EGJDAHIK;ADEFIJKL:EJIDAFLK;ADEFHJKL:HJEDAFLK;ADEFHIKL:HEIDAFLK;ADEFHIJL:HJEDAFLI;ADEFHIJK:HJEDAFIK;ADEFGJKL:EGJDAFLK;"
    "ADEFGIKL:EGIDAFLK;ADEFGIJL:EGJDAFLI;ADEFGIJK:EGJDAFIK;ADEFGHKL:HGEDAFLK;ADEFGHJL:HGJDAFLE;ADEFGHJK:HGJDAFEK;ADEFGHIL:HGEDAFLI;ADEFGHIK:HGEDAFIK;"
    "ADEFGHIJ:HGJDAFEI;ACGHIJKL:HJICAGLK;ACFHIJKL:HJICAFLK;ACFGIJKL:IGJCAFLK;ACFGHJKL:HGJCAFLK;ACFGHIKL:HGICAFLK;ACFGHIJL:HGJCAFLI;ACFGHIJK:HGJCAFIK;"
    "ACEHIJKL:EJICAHLK;ACEGIJKL:EJICAGLK;ACEGHJKL:EGJCAHLK;ACEGHIKL:EGICAHLK;ACEGHIJL:EGJCAHLI;ACEGHIJK:EGJCAHIK;ACEFIJKL:EJICAFLK;ACEFHJKL:HJECAFLK;"
    "ACEFHIKL:HEICAFLK;ACEFHIJL:HJECAFLI;ACEFHIJK:HJECAFIK;ACEFGJKL:EGJCAFLK;ACEFGIKL:EGICAFLK;ACEFGIJL:EGJCAFLI;ACEFGIJK:EGJCAFIK;ACEFGHKL:HGECAFLK;"
    "ACEFGHJL:HGJCAFLE;ACEFGHJK:HGJCAFEK;ACEFGHIL:HGECAFLI;ACEFGHIK:HGECAFIK;ACEFGHIJ:HGJCAFEI;ACDHIJKL:HJICADLK;ACDGIJKL:IGJCADLK;ACDGHJKL:HGJCADLK;"
    "ACDGHIKL:HGICADLK;ACDGHIJL:HGJCADLI;ACDGHIJK:HGJCADIK;ACDFIJKL:CJIDAFLK;ACDFHJKL:HJFCADLK;ACDFHIKL:HFICADLK;ACDFHIJL:HJFCADLI;ACDFHIJK:HJFCADIK;"
    "ACDFGJKL:CGJDAFLK;ACDFGIKL:CGIDAFLK;ACDFGIJL:CGJDAFLI;ACDFGIJK:CGJDAFIK;ACDFGHKL:HGFCADLK;ACDFGHJL:CGJDAFLH;ACDFGHJK:HGJCAFDK;ACDFGHIL:HGFCADLI;"
    "ACDFGHIK:HGFCADIK;ACDFGHIJ:HGJCAFDI;ACDEIJKL:EJICADLK;ACDEHJKL:HJECADLK;ACDEHIKL:HEICADLK;ACDEHIJL:HJECADLI;ACDEHIJK:HJECADIK;ACDEGJKL:EGJCADLK;"
    "ACDEGIKL:EGICADLK;ACDEGIJL:EGJCADLI;ACDEGIJK:EGJCADIK;ACDEGHKL:HGECADLK;ACDEGHJL:HGJCADLE;ACDEGHJK:HGJCADEK;ACDEGHIL:HGECADLI;ACDEGHIK:HGECADIK;"
    "ACDEGHIJ:HGJCADEI;ACDEFJKL:CJEDAFLK;ACDEFIKL:CEIDAFLK;ACDEFIJL:CJEDAFLI;ACDEFIJK:CJEDAFIK;ACDEFHKL:HEFCADLK;ACDEFHJL:HJFCADLE;ACDEFHJK:HJECAFDK;"
    "ACDEFHIL:HEFCADLI;ACDEFHIK:HEFCADIK;ACDEFHIJ:HJECAFDI;ACDEFGKL:CGEDAFLK;ACDEFGJL:CGJDAFLE;ACDEFGJK:CGJDAFEK;ACDEFGIL:CGEDAFLI;ACDEFGIK:CGEDAFIK;"
    "ACDEFGIJ:CGJDAFEI;ACDEFGHL:HGFCADLE;ACDEFGHK:HGECAFDK;ACDEFGHJ:HGJCAFDE;ACDEFGHI:HGECAFDI;ABGHIJKL:HJBAIGLK;ABFHIJKL:HJBAIFLK;ABFGIJKL:IJBFAGLK;"
    "ABFGHJKL:HJBFAGLK;ABFGHIKL:HGBAIFLK;ABFGHIJL:HJBFAGLI;ABFGHIJK:HJBFAGIK;ABEHIJKL:EJBAIHLK;ABEGIJKL:EJBAIGLK;ABEGHJKL:EJBAHGLK;ABEGHIKL:EGBAIHLK;"
    "ABEGHIJL:EJBAHGLI;ABEGHIJK:EJBAHGIK;ABEFIJKL:EJBAIFLK;ABEFHJKL:EJBFAHLK;ABEFHIKL:EIBFAHLK;ABEFHIJL:EJBFAHLI;ABEFHIJK:EJBFAHIK;ABEFGJKL:EJBFAGLK;"
    "ABEFGIKL:EGBAIFLK;ABEFGIJL:EJBFAGLI;ABEFGIJK:EJBFAGIK;ABEFGHKL:EGBFAHLK;ABEFGHJL:HJBFAGLE;ABEFGHJK:HJBFAGEK;ABEFGHIL:EGBFAHLI;ABEFGHIK:EGBFAHIK;"
    "ABEFGHIJ:HJBFAGEI;ABDHIJKL:IJBDAHLK;ABDGIJKL:IJBDAGLK;ABDGHJKL:HJBDAGLK;ABDGHIKL:IGBDAHLK;ABDGHIJL:HJBDAGLI;ABDGHIJK:HJBDAGIK;ABDFIJKL:IJBDAFLK;"
    "ABDFHJKL:HJBDAFLK;ABDFHIKL:HIBDAFLK;ABDFHIJL:HJBDAFLI;ABDFHIJK:HJBDAFIK;ABDFGJKL:FJBDAGLK;ABDFGIKL:IGBDAFLK;ABDFGIJL:FJBDAGLI;ABDFGIJK:FJBDAGIK;"
    "ABDFGHKL:HGBDAFLK;ABDFGHJL:HGBDAFLJ;ABDFGHJK:HGBDAFJK;ABDFGHIL:HGBDAFLI;ABDFGHIK:HGBDAFIK;ABDFGHIJ:HGBDAFIJ;ABDEIJKL:EJBAIDLK;ABDEHJKL:EJBDAHLK;"
    "ABDEHIKL:EIBDAHLK;ABDEHIJL:EJBDAHLI;ABDEHIJK:EJBDAHIK;ABDEGJKL:EJBDAGLK;ABDEGIKL:EGBAIDLK;ABDEGIJL:EJBDAGLI;ABDEGIJK:EJBDAGIK;ABDEGHKL:EGBDAHLK;"
    "ABDEGHJL:HJBDAGLE;ABDEGHJK:HJBDAGEK;ABDEGHIL:EGBDAHLI;ABDEGHIK:EGBDAHIK;ABDEGHIJ:HJBDAGEI;ABDEFJKL:EJBDAFLK;ABDEFIKL:EIBDAFLK;ABDEFIJL:EJBDAFLI;"
    "ABDEFIJK:EJBDAFIK;ABDEFHKL:HEBDAFLK;ABDEFHJL:HJBDAFLE;ABDEFHJK:HJBDAFEK;ABDEFHIL:HEBDAFLI;ABDEFHIK:HEBDAFIK;ABDEFHIJ:HJBDAFEI;ABDEFGKL:EGBDAFLK;"
    "ABDEFGJL:EGBDAFLJ;ABDEFGJK:EGBDAFJK;ABDEFGIL:EGBDAFLI;ABDEFGIK:EGBDAFIK;ABDEFGIJ:EGBDAFIJ;ABDEFGHL:HGBDAFLE;ABDEFGHK:HGBDAFEK;ABDEFGHJ:HGBDAFEJ;"
    "ABDEFGHI:HGBDAFEI;ABCHIJKL:IJBCAHLK;ABCGIJKL:IJBCAGLK;ABCGHJKL:HJBCAGLK;ABCGHIKL:IGBCAHLK;ABCGHIJL:HJBCAGLI;ABCGHIJK:HJBCAGIK;ABCFIJKL:IJBCAFLK;"
    "ABCFHJKL:HJBCAFLK;ABCFHIKL:HIBCAFLK;ABCFHIJL:HJBCAFLI;ABCFHIJK:HJBCAFIK;ABCFGJKL:CJBFAGLK;ABCFGIKL:IGBCAFLK;ABCFGIJL:CJBFAGLI;ABCFGIJK:CJBFAGIK;"
    "ABCFGHKL:HGBCAFLK;ABCFGHJL:HGBCAFLJ;ABCFGHJK:HGBCAFJK;ABCFGHIL:HGBCAFLI;ABCFGHIK:HGBCAFIK;ABCFGHIJ:HGBCAFIJ;ABCEIJKL:EJBAICLK;ABCEHJKL:EJBCAHLK;"
    "ABCEHIKL:EIBCAHLK;ABCEHIJL:EJBCAHLI;ABCEHIJK:EJBCAHIK;ABCEGJKL:EJBCAGLK;ABCEGIKL:EGBAICLK;ABCEGIJL:EJBCAGLI;ABCEGIJK:EJBCAGIK;ABCEGHKL:EGBCAHLK;"
    "ABCEGHJL:HJBCAGLE;ABCEGHJK:HJBCAGEK;ABCEGHIL:EGBCAHLI;ABCEGHIK:EGBCAHIK;ABCEGHIJ:HJBCAGEI;ABCEFJKL:EJBCAFLK;ABCEFIKL:EIBCAFLK;ABCEFIJL:EJBCAFLI;"
    "ABCEFIJK:EJBCAFIK;ABCEFHKL:HEBCAFLK;ABCEFHJL:HJBCAFLE;ABCEFHJK:HJBCAFEK;ABCEFHIL:HEBCAFLI;ABCEFHIK:HEBCAFIK;ABCEFHIJ:HJBCAFEI;ABCEFGKL:EGBCAFLK;"
    "ABCEFGJL:EGBCAFLJ;ABCEFGJK:EGBCAFJK;ABCEFGIL:EGBCAFLI;ABCEFGIK:EGBCAFIK;ABCEFGIJ:EGBCAFIJ;ABCEFGHL:HGBCAFLE;ABCEFGHK:HGBCAFEK;ABCEFGHJ:HGBCAFEJ;"
    "ABCEFGHI:HGBCAFEI;ABCDIJKL:IJBCADLK;ABCDHJKL:HJBCADLK;ABCDHIKL:HIBCADLK;ABCDHIJL:HJBCADLI;ABCDHIJK:HJBCADIK;ABCDGJKL:CJBDAGLK;ABCDGIKL:IGBCADLK;"
    "ABCDGIJL:CJBDAGLI;ABCDGIJK:CJBDAGIK;ABCDGHKL:HGBCADLK;ABCDGHJL:HGBCADLJ;ABCDGHJK:HGBCADJK;ABCDGHIL:HGBCADLI;ABCDGHIK:HGBCADIK;ABCDGHIJ:HGBCADIJ;"
    "ABCDFJKL:CJBDAFLK;ABCDFIKL:CIBDAFLK;ABCDFIJL:CJBDAFLI;ABCDFIJK:CJBDAFIK;ABCDFHKL:HFBCADLK;ABCDFHJL:CJBDAFLH;ABCDFHJK:HJBCAFDK;ABCDFHIL:HFBCADLI;"
    "ABCDFHIK:HFBCADIK;ABCDFHIJ:HJBCAFDI;ABCDFGKL:CGBDAFLK;ABCDFGJL:CGBDAFLJ;ABCDFGJK:CGBDAFJK;ABCDFGIL:CGBDAFLI;ABCDFGIK:CGBDAFIK;ABCDFGIJ:CGBDAFIJ;"
    "ABCDFGHL:CGBDAFLH;ABCDFGHK:HGBCAFDK;ABCDFGHJ:HGBCAFDJ;ABCDFGHI:HGBCAFDI;ABCDEJKL:EJBCADLK;ABCDEIKL:EIBCADLK;ABCDEIJL:EJBCADLI;ABCDEIJK:EJBCADIK;"
    "ABCDEHKL:HEBCADLK;ABCDEHJL:HJBCADLE;ABCDEHJK:HJBCADEK;ABCDEHIL:HEBCADLI;ABCDEHIK:HEBCADIK;ABCDEHIJ:HJBCADEI;ABCDEGKL:EGBCADLK;ABCDEGJL:EGBCADLJ;"
    "ABCDEGJK:EGBCADJK;ABCDEGIL:EGBCADLI;ABCDEGIK:EGBCADIK;ABCDEGIJ:EGBCADIJ;ABCDEGHL:HGBCADLE;ABCDEGHK:HGBCADEK;ABCDEGHJ:HGBCADEJ;ABCDEGHI:HGBCADEI;"
    "ABCDEFKL:CEBDAFLK;ABCDEFJL:CJBDAFLE;ABCDEFJK:CJBDAFEK;ABCDEFIL:CEBDAFLI;ABCDEFIK:CEBDAFIK;ABCDEFIJ:CJBDAFEI;ABCDEFHL:HFBCADLE;ABCDEFHK:HEBCAFDK;"
    "ABCDEFHJ:HJBCAFDE;ABCDEFHI:HEBCAFDI;ABCDEFGL:CGBDAFLE;ABCDEFGK:CGBDAFEK;ABCDEFGJ:CGBDAFEJ;ABCDEFGI:CGBDAFEI;ABCDEFGH:HGBCAFDE;"
)


# Round-of-32 bracket for the 12-group, best-third format. THIRD_FOR_X means the
# third-place opponent assigned to winner slot X by the table above.
ROUND_OF_32_MATCHES = (
    (73, "A2", "B2"),
    (74, "E1", "THIRD_FOR_E1"),
    (75, "F1", "C2"),
    (76, "C1", "F2"),
    (77, "I1", "THIRD_FOR_I1"),
    (78, "E2", "I2"),
    (79, "A1", "THIRD_FOR_A1"),
    (80, "L1", "THIRD_FOR_L1"),
    (81, "D1", "THIRD_FOR_D1"),
    (82, "G1", "THIRD_FOR_G1"),
    (83, "K2", "L2"),
    (84, "H1", "J2"),
    (85, "B1", "THIRD_FOR_B1"),
    (86, "J1", "H2"),
    (87, "K1", "THIRD_FOR_K1"),
    (88, "D2", "G2"),
)

# Fixed knockout tree after the round of 32. "W89" means the winner of match 89.
KNOCKOUT_MATCHES = (
    (89, "W74", "W77"),
    (90, "W73", "W75"),
    (91, "W76", "W78"),
    (92, "W79", "W80"),
    (93, "W83", "W84"),
    (94, "W81", "W82"),
    (95, "W86", "W88"),
    (96, "W85", "W87"),
    (97, "W89", "W90"),
    (98, "W93", "W94"),
    (99, "W91", "W92"),
    (100, "W95", "W96"),
    (101, "W97", "W98"),
    (102, "W99", "W100"),
    (104, "W101", "W102"),
)

teams = {
    "ARG": Team("ARG", "Argentina", 2114),
    "AUS": Team("AUS", "Australia", 1777),
    "AUT": Team("AUT", "Austria", 1830),
    "BEL": Team("BEL", "Belgium", 1893),
    "BIH": Team("BIH", "Bosnia and Herzegovina", 1595),
    "BRA": Team("BRA", "Brazil", 1991),
    "CAN": Team("CAN", "Canada", 1788),
    "CHE": Team("CHE", "Switzerland", 1891),
    "CIV": Team("CIV", "Cote d'Ivoire", 1695),
    "COD": Team("COD", "DR Congo", 1652),
    "COL": Team("COL", "Colombia", 1982),
    "CPV": Team("CPV", "Cape Verde", 1578),
    "CUW": Team("CUW", "Curacao", 1434),
    "CZE": Team("CZE", "Czechia", 1740),
    "DEU": Team("DEU", "Germany", 1932),
    "DZA": Team("DZA", "Algeria", 1760),
    "ECU": Team("ECU", "Ecuador", 1938),
    "EGY": Team("EGY", "Egypt", 1696),
    "ENG": Team("ENG", "England", 2021),
    "ESP": Team("ESP", "Spain", 2157),
    "FRA": Team("FRA", "France", 2063),
    "GHA": Team("GHA", "Ghana", 1510),
    "HRV": Team("HRV", "Croatia", 1911),
    "HTI": Team("HTI", "Haiti", 1548),
    "IRN": Team("IRN", "Iran", 1772),
    "IRQ": Team("IRQ", "Iraq", 1618),
    "JOR": Team("JOR", "Jordan", 1680),
    "JPN": Team("JPN", "Japan", 1906),
    "KOR": Team("KOR", "Korea Republic", 1758),
    "MAR": Team("MAR", "Morocco", 1827),
    "MEX": Team("MEX", "Mexico", 1875),
    "NLD": Team("NLD", "Netherlands", 1948),
    "NOR": Team("NOR", "Norway", 1914),
    "NZL": Team("NZL", "New Zealand", 1562),
    "PAN": Team("PAN", "Panama", 1730),
    "PRT": Team("PRT", "Portugal", 1986),
    "PRY": Team("PRY", "Paraguay", 1833),
    "QAT": Team("QAT", "Qatar", 1421),
    "SAU": Team("SAU", "Saudi Arabia", 1569),
    "SCO": Team("SCO", "Scotland", 1782),
    "SEN": Team("SEN", "Senegal", 1867),
    "SWE": Team("SWE", "Sweden", 1712),
    "TUN": Team("TUN", "Tunisia", 1628),
    "TUR": Team("TUR", "Turkey", 1910),
    "URY": Team("URY", "Uruguay", 1892),
    "USA": Team("USA", "United States", 1726),
    "UZB": Team("UZB", "Uzbekistan", 1714),
    "ZAF": Team("ZAF", "South Africa", 1518),
}


def create_rng(seed=None):
    return random.Random(seed)


def get_rng(rng):
    return rng if rng is not None else random


def win_prob_from_ratings(ra, rb, k=KNOCKOUT_K):
    return 1 / (1 + 10 ** ((rb - ra) / k))


def match_rating(code, rng=None, form_sigma=KNOCKOUT_FORM_SIGMA):
    rng = get_rng(rng)
    return teams[code].rating + rng.gauss(0, form_sigma)


def knockout_win_prob(a, b, rng=None, form_sigma=KNOCKOUT_FORM_SIGMA):
    ra = match_rating(a, rng, form_sigma)
    rb = match_rating(b, rng, form_sigma)
    return win_prob_from_ratings(ra, rb)


def poisson(lam, rng=None):
    rng = get_rng(rng)
    threshold = math.exp(-lam)
    product = 1.0
    goals = 0

    while product > threshold:
        goals += 1
        product *= rng.random()

    return goals - 1


def expected_goals(a, b, base=1.25, rating_scale=800, min_goals=0.20):
    diff = teams[a].rating - teams[b].rating
    a_expected = base + diff / rating_scale
    b_expected = base - diff / rating_scale
    return max(min_goals, a_expected), max(min_goals, b_expected)


def play_group_score(a, b, rng=None):
    a_expected, b_expected = expected_goals(a, b)
    return poisson(a_expected, rng), poisson(b_expected, rng)


def play_knockout_match(a, b, rng=None):
    rng = get_rng(rng)
    if rng.random() < knockout_win_prob(a, b, rng):
        return a
    return b


def create_group_table(group_codes, rng=None):
    rng = get_rng(rng)
    return {
        code: GroupStanding(code=code, tie_breaker=rng.random())
        for code in group_codes
    }


def record_group_match(table, a, b, goals_a, goals_b):
    table[a].goals_for += goals_a
    table[a].goals_against += goals_b
    table[b].goals_for += goals_b
    table[b].goals_against += goals_a

    if goals_a == goals_b:
        table[a].points += GROUP_DRAW_POINTS
        table[b].points += GROUP_DRAW_POINTS
        table[a].draws += 1
        table[b].draws += 1
        return

    winner = a if goals_a > goals_b else b
    loser = b if winner == a else a
    table[winner].points += GROUP_WIN_POINTS
    table[winner].wins += 1
    table[loser].losses += 1


def head_to_head_key(standing, tied_codes, match_results):
    code = standing.code
    tied_codes = set(tied_codes)
    points = 0
    goals_for = 0
    goals_against = 0

    for a, b, goals_a, goals_b in match_results:
        if a not in tied_codes or b not in tied_codes:
            continue
        if code == a:
            goals_for += goals_a
            goals_against += goals_b
            if goals_a > goals_b:
                points += GROUP_WIN_POINTS
            elif goals_a == goals_b:
                points += GROUP_DRAW_POINTS
        elif code == b:
            goals_for += goals_b
            goals_against += goals_a
            if goals_b > goals_a:
                points += GROUP_WIN_POINTS
            elif goals_a == goals_b:
                points += GROUP_DRAW_POINTS

    return points, goals_for - goals_against, goals_for


def rank_group_table(table, match_results):
    standings = sorted(
        table.values(),
        key=lambda standing: (
            standing.points,
            standing.goal_diff,
            standing.goals_for,
        ),
        reverse=True,
    )
    ranked = []
    index = 0

    while index < len(standings):
        base_key = (
            standings[index].points,
            standings[index].goal_diff,
            standings[index].goals_for,
        )
        tied = []
        while index < len(standings):
            candidate_key = (
                standings[index].points,
                standings[index].goal_diff,
                standings[index].goals_for,
            )
            if candidate_key != base_key:
                break
            tied.append(standings[index])
            index += 1

        if len(tied) == 1:
            ranked.extend(tied)
            continue

        tied_codes = [standing.code for standing in tied]
        ranked.extend(sorted(
            tied,
            key=lambda standing: (
                *head_to_head_key(standing, tied_codes, match_results),
                teams[standing.code].rating,
                standing.tie_breaker,
            ),
            reverse=True,
        ))

    return ranked


def draw_groups(rng=None):
    rng = get_rng(rng)
    codes = list(teams)
    rng.shuffle(codes)
    return {
        group_name: codes[index * GROUP_SIZE:(index + 1) * GROUP_SIZE]
        for index, group_name in enumerate(GROUP_NAMES)
    }


def simulate_group(group_codes, rng=None):
    table = create_group_table(group_codes, rng)
    match_results = []

    for i, a in enumerate(group_codes):
        for b in group_codes[i + 1:]:
            goals_a, goals_b = play_group_score(a, b, rng)
            record_group_match(table, a, b, goals_a, goals_b)
            match_results.append((a, b, goals_a, goals_b))

    return rank_group_table(table, match_results)


def simulate_group_stage_tables(rng=None):
    drawn_groups = draw_groups(rng)
    return {
        group_name: simulate_group(group_codes, rng)
        for group_name, group_codes in drawn_groups.items()
    }


def rank_third_place_entries(group_tables):
    third_place_entries = [
        (group_name, table[2])
        for group_name, table in group_tables.items()
    ]
    return sorted(
        third_place_entries,
        key=lambda entry: (
            entry[1].points,
            entry[1].goal_diff,
            entry[1].goals_for,
            entry[1].wins,
            teams[entry[1].code].rating,
            entry[1].tie_breaker,
        ),
        reverse=True,
    )


def build_third_place_assignments():
    assignments = {}

    for raw_entry in "".join(THIRD_PLACE_ASSIGNMENT_DATA).split(";"):
        if not raw_entry:
            continue

        advanced_groups, opponent_groups = raw_entry.split(":")
        assignments[advanced_groups] = {
            winner_slot: f"{opponent_group}3"
            for winner_slot, opponent_group in zip(
                THIRD_PLACE_TARGET_WINNER_SLOTS,
                opponent_groups,
            )
        }

    return assignments


THIRD_PLACE_ASSIGNMENTS = build_third_place_assignments()


def third_place_assignment_for(best_third_place_slots):
    key = "".join(sorted(slot[0] for slot in best_third_place_slots))

    if key not in THIRD_PLACE_ASSIGNMENTS:
        raise ValueError(f"unsupported third-place combination: {key}")

    return THIRD_PLACE_ASSIGNMENTS[key]


def resolve_knockout_slot(slot, group_stage_result, third_place_assignment):
    if slot.startswith("THIRD_FOR_"):
        winner_slot = slot.removeprefix("THIRD_FOR_")
        slot = third_place_assignment[winner_slot]

    if slot not in group_stage_result.qualifiers_by_slot:
        raise ValueError(f"unknown knockout slot: {slot}")

    return group_stage_result.qualifiers_by_slot[slot]


def resolve_knockout_ref(ref, group_stage_result, winners, third_place_assignment):
    if ref.startswith("W"):
        match_no = int(ref[1:])
        return winners[match_no]

    return resolve_knockout_slot(ref, group_stage_result, third_place_assignment)


def play_knockout_fixture(match_no, left, right, winners, rng=None):
    winner = play_knockout_match(left, right, rng)
    winners[match_no] = winner
    return winner


def create_stats():
    return {code: TeamStats() for code in teams}


def record_simulation(stats, result):
    for code in result.qualified:
        stats[code].qualified += 1
    for code in result.round_of_16:
        stats[code].round_of_16 += 1
    for code in result.quarterfinal:
        stats[code].quarterfinal += 1
    for code in result.semifinal:
        stats[code].semifinal += 1
    for code in result.final:
        stats[code].final += 1
    stats[result.champion].champion += 1


def make_simulation_result(group_stage_result, knockout_result):
    return SimulationResult(
        qualified=group_stage_result.qualified,
        round_of_16=knockout_result.round_of_16,
        quarterfinal=knockout_result.quarterfinal,
        semifinal=knockout_result.semifinal,
        final=knockout_result.final,
        champion=knockout_result.champion,
    )


def merge_stats(total, partial):
    if set(total) != set(partial):
        raise ValueError("stats tables must contain the same teams")

    for code in total:
        total[code].qualified += partial[code].qualified
        total[code].round_of_16 += partial[code].round_of_16
        total[code].quarterfinal += partial[code].quarterfinal
        total[code].semifinal += partial[code].semifinal
        total[code].final += partial[code].final
        total[code].champion += partial[code].champion


def simulate_batch(n, seed=None):
    stats = create_stats()
    rng = create_rng(seed)

    for _ in range(n):
        result = simulate_once(rng=rng)
        record_simulation(stats, result)

    return stats


def chunk_simulations(n, workers):
    if n < 1:
        raise ValueError("simulation count must be positive")

    chunk_count = min(n, max(1, workers * 20))
    base = n // chunk_count
    extra = n % chunk_count
    return [
        base + (1 if index < extra else 0)
        for index in range(chunk_count)
    ]


def make_chunk_seeds(seed, chunk_count):
    if seed is None:
        return [None] * chunk_count

    rng = create_rng(seed)
    return [
        rng.randrange(0, 2 ** 63)
        for _ in range(chunk_count)
    ]


def simulate_parallel(n, workers=None, seed=None):
    workers = workers or os.cpu_count() or 1
    workers = max(1, workers)
    chunks = chunk_simulations(n, workers)
    chunk_seeds = make_chunk_seeds(seed, len(chunks))
    stats = create_stats()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(simulate_batch, chunk, chunk_seed): chunk
            for chunk, chunk_seed in zip(chunks, chunk_seeds)
        }

        for future in as_completed(futures):
            partial_stats = future.result()
            merge_stats(stats, partial_stats)

    return stats


def format_stat(count, simulations):
    percentage = count / simulations * 100 if simulations else 0
    return f"{percentage:5.1f}%"


def print_stats(stats, simulations):
    rows = sorted(
        stats.items(),
        key=lambda item: (
            item[1].champion,
            item[1].final,
            item[1].semifinal,
            item[1].quarterfinal,
            item[1].round_of_16,
            item[1].qualified,
        ),
        reverse=True,
    )

    print("	".join([
        "Team",
        "Qualified",
        "Round of 16",
        "Quarterfinal",
        "Semifinal",
        "Final",
        "Champion",
    ]))
    for code, team_stats in rows:
        print(
            "	".join([
                f"{teams[code].name}({code})",
                format_stat(team_stats.qualified, simulations),
                format_stat(team_stats.round_of_16, simulations),
                format_stat(team_stats.quarterfinal, simulations),
                format_stat(team_stats.semifinal, simulations),
                format_stat(team_stats.final, simulations),
                format_stat(team_stats.champion, simulations),
            ])
        )


def simulate_once(rng=None):
    rng = rng if rng is not None else create_rng()
    group_stage_result = group_stage_sim(rng)
    knockout_result = knockout_stage_sim(group_stage_result, rng)
    return make_simulation_result(group_stage_result, knockout_result)


def group_stage_sim(rng=None):
    group_tables = simulate_group_stage_tables(rng)
    qualified = []
    qualifiers_by_slot = {}

    for group_name in GROUP_NAMES:
        table = group_tables[group_name]
        qualifiers_by_slot[f"{group_name}1"] = table[0].code
        qualifiers_by_slot[f"{group_name}2"] = table[1].code
        qualified.extend(standing.code for standing in table[:2])

    best_third_place_entries = rank_third_place_entries(group_tables)[:THIRD_PLACE_QUALIFIERS]
    best_third_place_slots = []

    for group_name, standing in best_third_place_entries:
        slot = f"{group_name}3"
        qualifiers_by_slot[slot] = standing.code
        best_third_place_slots.append(slot)
        qualified.append(standing.code)

    return GroupStageResult(
        qualified=qualified,
        qualifiers_by_slot=qualifiers_by_slot,
        best_third_place_slots=best_third_place_slots,
    )


def knockout_stage_sim(group_stage_result, rng=None):
    third_place_assignment = third_place_assignment_for(
        group_stage_result.best_third_place_slots
    )
    winners = {}

    for match_no, left_slot, right_slot in ROUND_OF_32_MATCHES:
        left = resolve_knockout_slot(left_slot, group_stage_result, third_place_assignment)
        right = resolve_knockout_slot(right_slot, group_stage_result, third_place_assignment)
        play_knockout_fixture(match_no, left, right, winners, rng)

    round_of_16 = [winners[match_no] for match_no in range(73, 89)]

    for match_no, left_ref, right_ref in KNOCKOUT_MATCHES:
        left = resolve_knockout_ref(left_ref, group_stage_result, winners, third_place_assignment)
        right = resolve_knockout_ref(right_ref, group_stage_result, winners, third_place_assignment)
        play_knockout_fixture(match_no, left, right, winners, rng)

    quarterfinal = [winners[match_no] for match_no in range(89, 97)]
    semifinal = [winners[match_no] for match_no in range(97, 101)]
    final = [winners[101], winners[102]]

    return KnockoutResult(
        round_of_16=round_of_16,
        quarterfinal=quarterfinal,
        semifinal=semifinal,
        final=final,
        champion=winners[104],
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Simulate the 12-group 2026 World Cup format and print team odds."
    )
    parser.add_argument(
        "simulations",
        type=int,
        help="number of tournament simulations to run",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=os.cpu_count() or 1,
        help="number of CPU worker threads to use",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="base random seed for reproducible runs",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.simulations < 1:
        raise SystemExit("simulations must be positive")
    if args.workers < 1:
        raise SystemExit("workers must be positive")

    stats = simulate_parallel(args.simulations, workers=args.workers, seed=args.seed)
    print_stats(stats, args.simulations)


if __name__ == "__main__":
    main()
