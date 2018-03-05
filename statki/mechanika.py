"""

    statki.mechanika
    ~~~~~~~~~~~~~~~~

    Mechanika i przebieg gry w rozbiciu na tury i rundy - wg opisu zawartego w meta/zasady.md. Gra składa się z tur, które składają się z rund. Runda odpowiada atakowi pojedynczego statku na pola planszy przeciwnika podzielonemu na salwy. Ilość salw oddawanych przez statek w rundzie zależy od jego aktualnej siły ognia. Tura składa się z tylu rund ile statków na planszy może atakować (nie są zatopione). Gra składa się z tak wielu tur, jak wiele razy po wykonaniu wszystkich ataków na planszy atakującego gracza pozostał jeszcze jakiś niezatopiony statek.

"""

from copy import deepcopy
from random import choice

from statki.plansza import Plansza, Pole, Salwa


class Gra:
    """
    Reprezentacja przebiegu gry na danej planszy. Zapisuje kolejne tury.
    """

    def __init__(self, plansza):
        self.plansza = plansza
        self.tura = Tura(self.plansza)
        self.tury = [self.tura]
        self.ofiary = []  # zatopione statki przeciwnika

    def dodaj_ture(self):
        """Tworzy nową turę i dodaje do listy tur"""
        self.tura = Tura(self.plansza)
        self.tury.append(self.tura)

    def podaj_info_o_rundzie(self):
        """Zwraca informację o rundzie w formacie: `tura #[liczba] / runda #[liczba] ([ilość statków])."""
        info = "tura #" + str(len(self.tury))
        info += " / runda #" + str(len(self.tura.rundy))
        info += " (" + str(len(self.tura.napastnicy)) + ")"
        return info  # w minuskule!

    def zrob_ruch(self):
        """
        Wykonuje ruch dla przeciwnika. Implementacja w klasach potomnych.
        """
        pass


class Tura:
    """
    Reprezentacja przebiegu tury. Zapisuje kolejne rundy i śledzi statki zdolne do ataku w kolejnych rundach. Startuje z listą niezatopionych statków.
    """

    def __init__(self, plansza):
        self.plansza = plansza
        self.migawki_planszy = [deepcopy(self.plansza)]  # +1 koniec każdej rundy
        self.napastnicy = self.plansza.niezatopione[:]  # śledzona jest tylko ilość elementów nie ich zawartość, więc wystarczy płytka kopia
        self.runda = Runda(self.napastnicy[0])
        self.rundy = [self.runda]

    def dodaj_runde(self):
        """Tworzy nową rundę i dodaje do listy rund"""
        self.napastnicy.remove(self.runda.napastnik)
        self.migawki_planszy.append(deepcopy(self.plansza))
        self.runda = Runda(self.napastnicy[0])
        self.rundy.append(self.runda)

    def filtruj_zatopione(self):
        """Filtruje z listy napastników statki zatopione w ostatniej rundzie przez przeciwnika."""
        aktualni_napastnicy = [napastnik for napastnik in self.napastnicy if napastnik not in self.plansza.zatopione]
        self.napastnicy = aktualni_napastnicy


class Runda:
    """
    Reprezentacja przebiegu rundy. Śledzi aktualnego napastnika i zapisuje salwy, które oddał oraz salwy otrzymane od przeciwnika. Startuje z pierwszym statkiem z listy napastników tury.
    """

    def __init__(self, statek):
        self.napastnik = statek
        self.sila_ognia = self.napastnik.sila_ognia[:]
        self.salwy_oddane = []
        self.salwy_otrzymane = []  # lista salw przeciwnika otrzymywana i zapisywana na początku rundy
        # flagi
        self.mozna_zmienic_napastnika = True
        self.mozna_atakowac = True

    def ustaw_napastnika(self, statek):
        """Ustawia podany statek jako aktualnego napastnika i jego siłę ognia jako aktualną dla rundy."""
        self.napastnik = statek
        self.sila_ognia = self.napastnik.sila_ognia[:]

    def dodaj_salwe_oddana(self, salwa):
        """Dodaje salwę, aktualizuje siłę ognia."""
        self.salwy_oddane.append(salwa)
        self.sila_ognia.remove(len(salwa))


class AI(Gra):
    """
    Reprezentacja przebiegu gry na danej planszy w wykonaniu komputera.

    Szkielet działania:
    ~~~~~~~~~~~~~~~~~~~
    1. Wybór napastnika.
    2. Wybór celu i orientacji salwy (polowanie lub celowanie).
    3. Oddanie salwy.
    Punkty 2-4 powtarzane są tak długo jak długo są salwy do oddania.

    To AI dokonuje prostych, losowych wyborów. Bardziej zaawansowana implementacja w klasach potomnych.
    """

    # KIERUNKI = ["E", "S", "W", "N", "NE", "SE", "SW", "NW"]
    # ORIENTACJE = ["•", "•• prawo", "╏ dół", "•• lewo", "╏ góra", "•••", "┇", "L", "Г", "Ꞁ", "⅃"]

    ORIENTACJE_SALWY = {
        Salwa.ORIENTACJE[0]: [],
        Salwa.ORIENTACJE[1]: [Plansza.KIERUNKI[0]],
        Salwa.ORIENTACJE[2]: [Plansza.KIERUNKI[1]],
        Salwa.ORIENTACJE[3]: [Plansza.KIERUNKI[2]],
        Salwa.ORIENTACJE[4]: [Plansza.KIERUNKI[3]],
        Salwa.ORIENTACJE[5]: [Plansza.KIERUNKI[0], Plansza.KIERUNKI[2]],
        Salwa.ORIENTACJE[6]: [Plansza.KIERUNKI[1], Plansza.KIERUNKI[3]],
        Salwa.ORIENTACJE[7]: [Plansza.KIERUNKI[0], Plansza.KIERUNKI[3]],
        Salwa.ORIENTACJE[8]: [Plansza.KIERUNKI[0], Plansza.KIERUNKI[1]],
        Salwa.ORIENTACJE[9]: [Plansza.KIERUNKI[1], Plansza.KIERUNKI[2]],
        Salwa.ORIENTACJE[10]: [Plansza.KIERUNKI[2], Plansza.KIERUNKI[3]]
    }
    ODWIEDZONE = [Pole.ZNACZNIKI["pudło"], Pole.ZNACZNIKI["trafione"], Pole.ZNACZNIKI["zatopione"]]

    def __init__(self, plansza_wlasna, plansza_gracza):
        super().__init__(plansza_wlasna)
        self.druga_plansza = deepcopy(plansza_gracza)

    def mysl(self):
        """
        Wybiera strategię ataku.
        """
        znaczniki = [pole.znacznik for rzad in self.druga_plansza.pola for pole in rzad]
        if Pole.ZNACZNIKI["trafione"] in znaczniki:
            self.celuj()
        else:
            self.poluj()

    def poluj(self):
        """
        Atakuje, nie wiedząc, gdzie jest ofiara.
        """
        wielkosc_salwy = self.tura.runda.napastnik.sila_ognia[0]
        pola = [pole for rzad in self.druga_plansza.pola for pole in rzad]
        wolne_pola = [pole for pole in pola if pole.znacznik not in self.ODWIEDZONE]
        cel = choice(wolne_pola)
        orientacja_salwy = self.wybierz_orientacje(cel)
        self.druga_plansza.odkryj_pola(orientacja_salwy)
        self.druga_plansza.oznacz_zatopione()
        self.tura.runda.dodaj_salwe_oddana(Salwa(
            self.tura.runda.napastnik.polozenie,
            orientacja_salwy,
            [None for i in range(wielkosc_salwy - len(orientacja_salwy))]
        ))

    def celuj(self):
        """
        Atakuje, wiedząc, gdzie jest ofiara.
        """
        pass

    def wybierz_orientacje(self, cel):
        """
        Wybiera najlepszą orientację salwy dla wskazanego celu. Przy ocenie bierze pod uwagę tylko ilość rażonych pól.
        """
        orientacje_salwy = []
        wielkosc_salwy = self.tura.runda.napastnik.sila_ognia[0]
        if wielkosc_salwy == 1:
            orientacje_salwy.append([cel])
        elif wielkosc_salwy == 2:
            for orientacja in Salwa.ORIENTACJE[1:5]:
                orientacje_salwy.append(self.podaj_pola_salwy(cel, self.ORIENTACJE_SALWY[orientacja]))
        elif wielkosc_salwy == 3:
            for orientacja in Salwa.ORIENTACJE[5:]:
                orientacje_salwy.append(self.podaj_pola_salwy(cel, self.ORIENTACJE_SALWY[orientacja]))

        return sorted(orientacje_salwy, key=lambda o: len([pole for pole in o if pole.znacznik not in self.ODWIEDZONE]), reverse=True)[0]

    def podaj_pola_salwy(self, cel, kierunki):
        """Podaje pola salwy wg podanego celu."""
        pola_salwy = [cel]
        for kierunek in kierunki:
            sasiad = self.druga_plansza.podaj_sasiednie_pole(cel, kierunek)
            if sasiad is not None:
                pola_salwy.append(sasiad)
        return pola_salwy

    def wybierz_napastnika(self):
        """
        Wybiera napastnika. Wybierany jest statek posiadający największą siłę ognia w danej rundzie.
        """
        napastnik = sorted(self.tura.napastnicy, key=lambda s: sum(s.sila_ognia), reverse=True)[0]
        self.tura.runda.ustaw_napastnika(napastnik)

    def zrob_ruch(self):
        """
        Wykonuje ruch dla przeciwnika. Wybiera napastnika, wymyśla i oddaje salwy, dodaje kolejną rundę/turę.
        """
        self.wybierz_napastnika()
        while len(self.tura.runda.sila_ognia) > 0:
            self.mysl()
        self.dodaj_ture() if len(self.tura.napastnicy) == 1 else self.tura.dodaj_runde()


class MocneAI(AI):
    """
    AI wykorzystujące do polowania i celowania symulację statystycznego występowania statków na planszy.

    Inspiracja algorytmu pochodzi z tego artykułu dotyczącego zwyczajnych Statków (w wersji amerykańskiej - statki tylko 2-5 pól, ortogonalnie, możliwość stykania się): http://www.datagenetics.com/blog/december32011/index.html
    """

    def __init__(self, plansza_wlasna, plansza_gracza):
        super().__init__(plansza_wlasna)
        self.druga_plansza = deepcopy(plansza_gracza)

    def wybierz_orientacje(self, cel):
        """
        Wybiera najlepszą orientację salwy dla wskazanego celu. Przy ocenie bierze pod uwagę tylko ilość rażonych pól.
        """

        pass  # TODO: przeładowanie metody rodzica


class GraSieciowa(Gra):  # TODO
    """
    Reprezentacja przebiegu gry na danej planszy w wykonaniu drugiego gracza połączonego przez sieć.
    """

    def __init__(self, plansza_wlasna, plansza_gracza):
        super().__init__(plansza_wlasna)
        self.druga_plansza = deepcopy(plansza_gracza)

    def zrob_ruch(self):
        """
        Wykonuje ruch dla przeciwnika. Pobiera salwy przez sieć od drugiego gracza i dodaje rundę/turę.
        """
        pass

    def pobierz_salwy_oddane(self):
        """
        Pobiera przez sieć salwy oddane przez drugiego gracza.
        """
        pass
