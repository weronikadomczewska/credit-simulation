from client_database import *
from copy import deepcopy


class Simulation:
    """
    Klasa przeprowadza symulację pożyczek na danych dostarczonych przez klasę ClientDatabase.
    interest_rate_distribution - rozkład stopy procentowej (w procentach)
    bank_margin - marża banku
    interest_rate - stopa procentowa na moment podejmowania decyzji kredytowej
    """

    def __init__(self, interest_rate_distribution: str, maintenance_cost_distribution: str,
                 bank_margin: float, interest_rate: float, number_of_clients: int):
        self.interest_rate_distribution = interest_rate_distribution
        self.bank_margin = bank_margin
        self.interest_rate = interest_rate
        self.maintenance_cost_distribution = maintenance_cost_distribution
        self.number_of_clients = number_of_clients


    def check(self, age: int, months_loan_duration: int, amount: int,
              earnings_netto: float, maintenance_cost: float):
        """
        Funkcja sprawdza na podstawie podanych parametrów (wiek kredytobiorcy, zarobki, wysokość pożyczki,
        okres kredytowania, wysokość potencjalnej raty oraz wydatki kredytobiorcy) czy klient może dostać pożyczkę.
        Ograniczenia:
        - (earnings_netto - maintenance_cost)/2 >= loan_installment zgodnie z zaleceniami knf
        - age + month_loan_duration <= 65 - chcemy spłaty przed wiekiem emerytalnym
        Funkcja zwraca 1, gdy klient o dnaych parametrach spełnia warunki i 0 w przeciwnym razie
        """

        loan_installment = self.calc_loan_installment(amount, months_loan_duration, self.interest_rate)
        if age + round((months_loan_duration / 12), 2) > 65 or (earnings_netto - maintenance_cost)/2 <= loan_installment:
            return 0
        return 1

    def choose_maintenance_cost(self):
        """
        Funkcja wybiera koszty utrzymania klienta (chosen_maintenance_cost) ze zbioru liczb uzyskanych z
        podanego rozkładu (normalnego, jednostajnego lub gamma).
        Parametry rozkładów wzięte z danych statystycznych dla życia na średnim poziomie.
        Rozład normalny: średnia 2317 zł, odchylenie std. 913 zł
        Rozkład jednostajny: dolna granica 1404 zł, górna granica 3230 zł (średnia +- odchylenie std.)
        Rozkład gamma: shape: pierwiastek ze średniej, scale: odchylenie standardowe / pierwiastek ze średniej
        """
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
                np.random.uniform(lower, upper, self.number_of_clients)), 2)
        else:
            chosen_maintenance_cost = round(random.choice(
                np.random.gamma(shape, scale, self.number_of_clients)), 2)
        return chosen_maintenance_cost

    def calc_loan_installment(self, amount, months_loan_duration, interest_rate: float):
        """
        :param amount: wysokość pożyczki
        :param months_loan_duration: okres kredytowania (w miesiącach)
        :param interest_rate: aktualna stopa procentowa
        :return: kwota raty w danym miesiącu
        """
        return round(((amount * (1 + self.bank_margin/100)**(months_loan_duration/12) +
                            (amount * (1 + interest_rate/100)**(months_loan_duration/12))))/months_loan_duration, 2)

    def choose_clients(self, clients_data: list[dict]):
        """
        Funkcja zwraca listę informacji o klientach, którzy spełniają warunki na przyznanie pożyczki
        """
        chosen_clients = []
        for data in clients_data:
            if self.check(data["age"], data["months_loan_duration"],
                          data["amount"], data["earnings_netto"], data["maintenance_cost"]):
                loan_installment = self.calc_loan_installment(data["amount"],
                                                              data["months_loan_duration"], self.interest_rate)
                data["loan_installment"] = loan_installment
                chosen_clients.append(data)
        return chosen_clients

    def calc_bank_income(self, client_data):
        """
        :param client_data: dane klienta w danym miesiącu
        :return: zysk banku od danego klienta w danym miesiącu
        """
        return round(client_data["amount"] * self.bank_margin/100, 2)

    def calc_possible_interest_rates(self, longest_months_loan_duration):
        """
        Funkcja losuje tyle możliwych zmian stóp procentowych, ile najdłuższy okres kredytowania wśród klientów
        stopy procentowe są losowane z wybranego przez użytkownika rozkładu
        parametry rozkładów:
        - jednostajny: wartość najmniejsza 0%, wartość największa 18%
        - normalny: średnia 7.38%, odchylenie std. 5.7%
        - gamma: shape: pierwiastek ze średniej, scale: odchylenie standardowe / pierwiastek ze średniej
        """
        mean = 7.38
        standard_deviation = 5.7
        lower = 0.0
        upper = 18.0
        shape = round(mean ** (1 / 2), 2)
        scale = shape
        if self.interest_rate_distribution == "uniform":
            possible_interest_rates = np.random.uniform(lower, upper, longest_months_loan_duration + 1)
        elif self.interest_rate_distribution == "normal":
            possible_interest_rates = np.random.normal(mean, standard_deviation, longest_months_loan_duration + 1)
        else:
            possible_interest_rates = np.random.gamma(shape, scale, longest_months_loan_duration + 1)

        return possible_interest_rates

    def simulate_single_client_month(self, client_data: dict, interest_rate: float):
        """
        :param client_data: słownik z danymi klienta z poprzedniego miesiąca spłacania pożyczki
        :return: dane klienta po aktualnym miesiącu
        """
        new_maintenance_cost = self.choose_maintenance_cost()
        new_loan_installment = self.calc_loan_installment(client_data["amount"],
                                                          client_data["months_loan_duration"], interest_rate)
        new_client_data = deepcopy(client_data)
        new_client_data["maintenance_cost"] = new_maintenance_cost
        new_client_data["loan_installment"] = new_loan_installment
        # warunek bankructwa
        if (client_data["earnings_netto"] - new_maintenance_cost) / 2 <= new_loan_installment:
            new_client_data["is_bankrupt"] = True
        return new_client_data

    def simulate(self, chosen_clients_data: list[dict]):
        """
        :param chosen_clients_data: lista słowników z danymi klientów, którzy dostali pożyczkę
        :return: procent klientów, którzy zbankrutowali podczas spłaty pożyczki, zysk banku
        Funkcja przeprowadza symulację spłacania pożyczki dla klientów banku, którzy ją otrzymali
        Sposób 1 na bankruta: w momencie, gdy klient raz nie zapłaci raty, zostaje bankrutem
        """
        longest_months_loan_duration = max(client["months_loan_duration"] for client in chosen_clients_data)
        bankrupts = 0
        bank_incomes = np.zeros(longest_months_loan_duration+1)
        client_infos = []
        possible_interest_rates = self.calc_possible_interest_rates(longest_months_loan_duration)
        for client_data in chosen_clients_data:
            months_loan_duration = client_data["months_loan_duration"]
            # informacje o kliencie w każdym miesiącu spłaty
            loan_repayment_process_info = []
            # zakładamy na początku, że klient nie jest bankrutem
            is_bankrupt = False
            for month in range(1, months_loan_duration+1):
                interest_rate = possible_interest_rates[month]
                new_client_data = self.simulate_single_client_month(client_data, interest_rate)
                loan_repayment_process_info.append(new_client_data)
                bank_incomes[month] += self.calc_bank_income(client_data)
                if new_client_data["is_bankrupt"]:
                    is_bankrupt = True
                    bank_incomes[month] -= self.calc_bank_income(client_data)
                    break
            if is_bankrupt:
                bankrupts += 1
            client_infos.append(loan_repayment_process_info)
        return bankrupts, round(sum(bank_incomes), 2)
    def simulate2(self, chosen_clients_data: list[dict]):
        """
        :param chosen_clients_data: lista słowników z danymi klientów, którzy dostali pożyczkę
        :return: procent klientów, którzy zbankrutowali podczas spłaty pożyczki, zysk banku
        Funkcja przeprowadza symulację spłacania pożyczki dla klientów banku, którzy ją otrzymali
        Sposób 2 na bankruta: w momencie, gdy klient pierwszy raz nie zapłaci raty, zwiększamy mu ją o odsetki,
        gdy nie zapłaci drugi raz, następna rata też jest z odsetkami, kiedy dalej nie zapłaci, staje się bankrutem
        """
        longest_months_loan_duration = max(client["months_loan_duration"] for client in chosen_clients_data)
        bankrupts = 0
        client_infos = []
        bank_incomes = np.zeros(longest_months_loan_duration + 1)
        # losuję tyle możliwych zmian stóp procentowych, ile najdłuższy okres kredytowania wśród klientów
        possible_interest_rates = self.calc_possible_interest_rates(longest_months_loan_duration)
        for client_data in chosen_clients_data:
            months_loan_duration = client_data["months_loan_duration"]
            # informacje o kliencie w każdym miesiącu spłaty
            loan_repayment_process_info = []
            # zakładamy na początku, że klient nie jest bankrutem
            is_bankrupt = False
            # zliczamy niezapłacone raty
            unpaid_installments = 0
            for month in range(1, months_loan_duration+1):
                interest_rate = possible_interest_rates[month]
                # gdy klient nie zapłacił raty raz lub dwa, dostaje ratę z odsetkami 10%
                if unpaid_installments == 1 or unpaid_installments == 2:
                    interest_rate += interest_rate * 0.1
                new_client_data = self.simulate_single_client_month(client_data, interest_rate)
                if new_client_data["is_bankrupt"]:
                    unpaid_installments += 1
                    if unpaid_installments == 3:
                        is_bankrupt = True
                        bank_incomes[month] -= self.calc_bank_income(client_data)
                        break
                loan_repayment_process_info.append(new_client_data)
                bank_incomes[month] += self.calc_bank_income(client_data)
            client_infos.append(loan_repayment_process_info)
            if is_bankrupt:
                bankrupts += 1
        return bankrupts, round(sum(bank_incomes), 2)


if __name__ == "__main__":
    DATAPATH = "data/credit.csv"
    number_of_clients = 1000
    maintenance_cost_distribution = "normal"
    interest_rate_distribution = "normal"
    bank_margin = 6.0
    beginning_interest_rate = 6.5
    # while number_of_clients is None:
    #     try:
    #         number_of_clients = int(input("Podaj ilość klientów: "))
    #     except ValueError:
    #         raise ValueError(f"Incorrect value given ({number_of_clients}), expected integer value")
    # while len(maintenance_cost_distribution) == 0 or maintenance_cost_distribution not in ["uniform", "normal", "gamma"]:
    #     try:
    #         maintenance_cost_distribution = input("Podaj rozkład kosztów utrzymania (uniform, normal, gamma): ")
    #     except ValueError:
    #         raise ValueError(f"Incorrect value given ({maintenance_cost_distribution}),
    #         expected uniform, normal or gamma")
    # while len(interest_rate_distribution) == 0 or interest_rate_distribution not in ["uniform", "normal", "gamma"]:
    #     try:
    #         interest_rate_distribution= input("Podaj rozkład stopy procentowej (uniform, normal, gamma): ")
    #     except ValueError:
    #         raise ValueError(f"Incorrect value given ({interest_rate_distribution}),
    #         expected uniform, normal or gamma")
    # while bank_margin is None:
    #     try:
    #         bank_margin = float(input("Podaj marżę banku (w %): "))
    #     except ValueError:
    #         raise ValueError(f"Incorrect value given ({bank_margin}), expected float value")
    # while beginning_interest_rate is None:
    #     try:
    #         beginning_interest_rate = float(input("Podaj początkową stopę procentową (w %): "))
    #     except ValueError:
    #         raise ValueError(f"Incorrect value given ({beginning_interest_rate}), expected float value")

    cdb = ClientDatabase(number_of_clients, maintenance_cost_distribution)
    simulation = Simulation(interest_rate_distribution, maintenance_cost_distribution, bank_margin,
                            beginning_interest_rate, number_of_clients)
    possible_clients_data = cdb.prepare_entry_data(DATAPATH, number_of_clients)
    print(f"possible clients data: {len(possible_clients_data)}")
    print("------")
    chosen_clients_data = simulation.choose_clients(possible_clients_data)
    print(f"chosen clients data: {len(chosen_clients_data)}")
    print("------")
    print(f"bankrupts (1st way): {simulation.simulate(chosen_clients_data)[0]}")
    print(f"total bank income: {simulation.simulate(chosen_clients_data)[1]}")
    print("------")
    print(f"bankrupts (2nd way): {simulation.simulate2(chosen_clients_data)[0]}")
    print(f"total bank income: {simulation.simulate2(chosen_clients_data)[1]}")
