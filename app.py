from client_database import *


class Simulation:

    def __init__(self, interest_rate_distribution: str, bank_margin: float, interest_rate: float):
        self.interest_rate_distribution = interest_rate_distribution
        self.bank_margin = bank_margin
        self.interest_rate = interest_rate

    def check(self, age: int, month_loan_duration: int, amount: int,
              earnings_netto: float, maintenance_cost: float):
        '''
        Funkcja sprawdza na podstawie podanych parametrów (wiek kredytobiorcy, zarobki, wysokość pożyczki,
        okres kredytowania, wysokość potencjalnej raty oraz wydatki kredytobiorcy) czy klient może dostać pożyczkę.
        Ograniczenia:
        - (earnings_netto - maintenance_cost)/2 >= loan_installment zgodnie z zaleceniami knf
        - age + month_loan_duration <= 65 - chcemy spłaty przed wiekiem emerytalnym
        Funkcja zwraca 1, gdy klient o dnaych parametrach spełnia warunki i 0 w przeciwnym razie
        '''

        loan_installment = ((amount * (1 + self.bank_margin)**(month_loan_duration/12) +
                            (amount * (1 + self.interest_rate)**(month_loan_duration/12))))/month_loan_duration
        print(f"Calculated loan installment (while making decision): {loan_installment}")
        if age + round((month_loan_duration / 12), 2) > 65 or (earnings_netto - maintenance_cost)/2 >= loan_installment:
            return 0
        return 1



if __name__ == "__main__":
    DATAPATH = "data/credit.csv"
    number_of_clients = 100
    maintenance_cost_distribution = "normal"
    interest_rate_distribution = "normal"
    bank_margin = 6.0
    beginning_interest_rate = 0.5
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

    cdb = ClientDatabase(number_of_clients, maintenance_cost_distribution)
    print(cdb.prepare_entry_data(DATAPATH))
