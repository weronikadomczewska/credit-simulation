import csv
import random
import numpy as np


# class Client:
#     def __init__(self, maintenance_cost_distribution: str):
#         self.amount = 0
#         self.age = 0
#         self.months_loan_duration = 0
#         self.is_bankrupt = False
#         self.maintenance_cost = 0
#         self.maintenance_cost_distribution = maintenance_cost_distribution
#         self.earnings_brutto = 0
#
#     def __repr__(self):
#         return self.__dict__

class ClientDatabase:

    def __init__(self, number_of_clients: int, maintenance_cost_distribution: str):
        self.clients = []
        self.number_of_clients = number_of_clients
        self.maintenance_cost_distribution = maintenance_cost_distribution

    def choose_maintenance_cost(self):
        '''
        Funkcja wybiera koszty utrzymania klienta (chosen_maintenance_cost) ze zbioru liczb uzyskanych z
        podanego rozkładu (normalnego, jednostajnego lub gamma).
        Parametry rozkładów wzięte z danych statystycznych dla życia na średnim poziomie.
        Rozład normalny: średnia 2317 zł, odchylenie std. 913 zł
        Rozkład jednostajny: dolna granica 1404 zł, górna granica 3230 zł (średnia +- odchylenie std.)
        Rozkład gamma: shape: pierwiastek ze średniej, scale: odchylenie standardowe / pierwiastek ze średniej

        '''

        mean = 2317
        standard_deviation = 913
        lower = 1404
        upper = 3230
        shape = round(mean ** (1/2), 2)
        scale = shape
        if self.maintenance_cost_distribution.lower() == "normal":
            chosen_maintenance_cost = round(random.choice(
                np.random.normal(mean, standard_deviation, self.number_of_clients)), 2)
        elif self.maintenance_cost_distribution.lower() == "uniform":
            chosen_maintenance_cost = round(random.choice(
                np.random.normal(lower, upper, self.number_of_clients)), 2)
        else:
            chosen_maintenance_cost = round(random.choice(
                np.random.normal(shape, scale, self.number_of_clients)), 2)
        return chosen_maintenance_cost

    def prepare_entry_data(self, datasource: str):
        '''
        Funkcja pobiera dane z pliku credit.csv, który zawiera dane klienta: wiek (age), wysokość pożyczki (amount) oraz
        okres kredytowania w miesiącach (month_loan_duration).
        Zarobki brutto klienta są losowane z rozkładu normalnego o parametrach średnia: 6857 zł, odchylenie std. 1200 zł
        Zarobki netto klienta są wyliczane na podstawie podanych w prawie stawekw podatkowych (17% lub 32%).
        Celem jest przygotowanie danych klienta na potrzeby podjęcia decyzji, czy przyznajemy pożyczkę
        '''

        data_list = []
        with open(datasource, newline="") as csvfile:
            data = csv.reader(csvfile)
            headers = next(data)
            for row in data:
                row_dict = dict(zip(headers, row))
                data_list.append(row_dict)

        earnings_mean = 6857
        earnings_std_deviation = 1200

        # przeglądam dane; client_data to dane potencjalnego klienta na początku spłacania kredytu
        for client_data in data_list:
            chosen_client_data = {"months_loan_duration": client_data["months_loan_duration"],
                                  "amount": client_data["amount"], "age": client_data["age"],
                                  "earnings_brutto": round(random.choice(
                                      np.random.normal(earnings_mean, earnings_std_deviation, self.number_of_clients)))}

            # ustalenie, czy dochód brutto obowiązuje podatek 17% czy 32% (warunek: roczne zarobki większe lub mniejsze
            # od 85528 złotych
            if chosen_client_data["earnings_brutto"] * 12 < 85528:
                chosen_client_data["earnings_netto"] = round(
                    chosen_client_data["earnings_brutto"] - chosen_client_data["earnings_brutto"] * 0.17, 2)
            else:
                chosen_client_data["earnings_netto"] = round(
                    chosen_client_data["earnings_brutto"] - chosen_client_data["earnings_brutto"] * 0.32, 2)
            # pytanie - dlaczego dla rozkładu uniform i normal wychodzą wartości ujemne mimo podanych parametrów?
            # pytanie - dlaczego dla rozkładu gamma wychodzą bardzo małe wartości (od około 10 do 100)?
            # jak wyznaczyć parametry tego rozkładu?
            chosen_client_data["maintenance_cost"] = abs(self.choose_maintenance_cost())
            # na początku symulacji żaden klient nie jest bankrutem
            chosen_client_data["is_bankcrupt"] = False
            self.clients.append(chosen_client_data)
        return self.clients


if __name__ == "__main__":
    cdb = ClientDatabase(100, "normal")
    print(cdb.prepare_entry_data("data/credit.csv"))