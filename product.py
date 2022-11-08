import pandas as pd
import random
import warnings
import sys

if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

from beautifultable import BeautifulTable

# reading assumptions
assumptions_df = pd.read_csv('data/assumptions.csv')

# accessing mortality rates
male_mortality_rates = pd.read_csv("data/male_mortality_rates.csv")
female_mortality_rates = pd.read_csv("data/female_mortality_rates.csv")

person_age = 25
person_gender = input("Person's Gender (M or F): ")
premium = 2489947.936
profit_margin = 0
term_length = 13

def vlookup(value,df,coli,colo):
    """ 
    vlookup function to reference other tables
    """
    return next(iter(df.loc[df[coli]==value][colo]), None)

profit_margin_table = BeautifulTable()
premium_rate_table = BeautifulTable()
# terms = ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"]
# table.column_headers = terms
profit_margins = []
new_profit_margins = []
premium_rates = []
ages = []
new_age = person_age

for s in range(13):
    ages.append(new_age)
    new_age = new_age + 1
    
profit_margin_table.columns.insert(0,ages,header='')
premium_rate_table.columns.insert(0,ages,header='')

for t in range(10):
    #print(term_length)
    for k in range(13):
        def create_male_decrements_table():
            "function to create the male decrements table"
            
            male_decrements_table = []

            age = person_age
            
            for i in range(term_length):
                qxd = vlookup(age,male_mortality_rates,'age','qxd')
                qxr = vlookup(age,male_mortality_rates,'age','qxr')
                if (qxd or qxr) is not None:
                    aqxd = qxd * (1 - 0.5 * qxr)
                    aqxr = qxr * (1 - 0.5 * qxd)
                    apx = 1 - (aqxd + aqxr)
                else:
                    aqxd = 0
                    aqxr = 0
                    apx = 0

                
                if i == 0:
                    t_1apx = 1
                else:
                    t_1apx = (male_decrements_table[i-1]['apx'])*(male_decrements_table[i-1]['t_1apx'])
                
                male_decrements_table.append({
                    'age': age,
                    'qxd': qxd,
                    'qxr': qxr,
                    'aqxd': aqxd,
                    'aqxr': aqxr,
                    'apx': apx,
                    't_1apx': t_1apx
                })
                age = age + 1
                    
            return pd.DataFrame(male_decrements_table) 


        def create_female_decrements_table():
            "function to create the female decrements table"
            
            female_decrements_table = []

            age = person_age
            
            for i in range(term_length):
                qxd = vlookup(age,female_mortality_rates,'age','qxd')
                qxr = vlookup(age,female_mortality_rates,'age','qxr')
                if (qxd or qxr) is not None:
                    aqxd = qxd * (1 - 0.5 * qxr)
                    aqxr = qxr * (1 - 0.5 * qxd)
                    apx = 1 - (aqxd + aqxr)
                else:
                    aqxd = 0
                    aqxr = 0
                    apx = 0
                
                if i == 0:
                    t_1apx = 1
                else:
                    t_1apx = (female_decrements_table[i-1]['apx'])*(female_decrements_table[i-1]['t_1apx'])
                
                female_decrements_table.append({
                    'age': age,
                    'qxd': qxd,
                    'qxr': qxr,
                    'aqxd': aqxd,
                    'aqxr': aqxr,
                    'apx': apx,
                    't_1apx': t_1apx
                })
                age = age + 1
                    
            return pd.DataFrame(female_decrements_table) 

        #create decrements table based on person's gender
        if person_gender == "M":
            decrements_table = create_male_decrements_table()
            pricing_values = pd.read_csv("data/male_pricing_defaults.csv")
        else:
            decrements_table = create_female_decrements_table()
            pricing_values = pd.read_csv("data/female_pricing_defaults.csv")

        def create_table_with_qx_lx_dx():
            "function to calculate dx and lx"
            
            qx_lx_dx = []
            age = 25
            
            for i in range(term_length):
                qx = vlookup(age,pricing_values,'age','qx')
                
                if i == 0:
                    lx = 100000
                else:
                    lx = qx_lx_dx[i-1]['lx'] - qx_lx_dx[i-1]['dx']
                
                dx = qx * lx
                
                qx_lx_dx.append({
                    'age': age,
                    'qx': qx,
                    'lx': lx,
                    'dx': dx
                })
                age = age + 1
            return pd.DataFrame(qx_lx_dx)

        table_with_qx_lx_dx = create_table_with_qx_lx_dx()

        pricing_interest = 0.08
        sum_assured = 10000000
        V = 1/(1+pricing_interest)


        def calculate_benefit_and_claim_expenses():
            "function to calculate benefit and claims expenses"
            
            benefit_and_claims = []
            
            for i in range(term_length):
                time = i + 1
                discount = V ** time
                lookup_age = person_age + i
                lookup_prob = vlookup(lookup_age,pricing_values,'age','probability')
                if lookup_prob is None:
                    probability = 0
                else:
                    probability =  lookup_prob
                EPV = sum_assured * discount * probability
                
                benefit_and_claims.append({
                    "time t": time,
                    "amount": sum_assured,
                    "discount": discount,
                    "probability": probability,
                    "EPV": EPV
                })
            lookup_age = person_age + 4  
            lookup_lx = vlookup(lookup_age,table_with_qx_lx_dx,'age','lx') 
            if lookup_lx is None:
                last_probability = 0
            else:
                last_probability =  lookup_lx / table_with_qx_lx_dx.lx[0]
            benefit_and_claims.append({
                    "time t": time,
                    "amount": sum_assured,
                    "discount": discount,
                    "probability": last_probability,
                    "EPV": sum_assured * discount * last_probability
                })
            return pd.DataFrame(benefit_and_claims)
                
        benefit_and_claim_expenses = calculate_benefit_and_claim_expenses()

        # EPV of benefits and claims
        EPV_benefits = round(sum(benefit_and_claim_expenses.EPV), 2)


        def calculate_initial_and_regular_expenses():
            "function to calculate initial and regular expenses"
            
            initial_and_regular_expenses = []
            
            for i in range(term_length):
                if i == 0:
                    amount = 0.4 * premium
                else:
                    amount = 0.05 * premium
                    
                discount = V ** i
                lookup_age = person_age + i
                lookup_lx = vlookup(lookup_age,table_with_qx_lx_dx,'age','lx') 
                if lookup_lx is None:
                    probability = 0
                else:
                    probability =  lookup_lx / table_with_qx_lx_dx.lx[0]
                EPV = amount * discount * probability
                
                initial_and_regular_expenses.append({
                    "time t": i,
                    "amount": amount,
                    "discount": discount,
                    "probability": probability,
                    "EPV": EPV
                })
                
            return pd.DataFrame(initial_and_regular_expenses)


        initial_and_regular_expenses = calculate_initial_and_regular_expenses()

        # EPV of initial and regular expenses
        EPV_expenses = round(sum(initial_and_regular_expenses.EPV), 2)


        def calculate_initial_and_renewal_commission():
            "function to calculate initial and renewal commission"
            
            initial_and_renewal_commission = []
            
            for i in range(term_length):
                if i == 0:
                    amount = 0.4 * premium
                else:
                    amount = 0.08 * premium
                    
                discount = V ** i
                lookup_age = person_age + i
                lookup_lx = vlookup(lookup_age,table_with_qx_lx_dx,'age','lx') 
                if lookup_lx is None:
                    probability = 0
                else:
                    probability =  lookup_lx / table_with_qx_lx_dx.lx[0]
                EPV = amount * discount * probability
                
                initial_and_renewal_commission.append({
                    "time t": i,
                    "amount": amount,
                    "discount": discount,
                    "probability": probability,
                    "EPV": EPV
                })
                
            return pd.DataFrame(initial_and_renewal_commission)

        initial_and_renewal_commission = calculate_initial_and_renewal_commission()


        #EPV of initial and renewal commission
        EPV_commission = round(sum(initial_and_renewal_commission.EPV), 2)


        def calculate_premiums():
            "function to calculate premiums"
            
            premiums = []
            
            for i in range(term_length):            
                discount = V ** i
                lookup_age = person_age + i
                lookup_lx = vlookup(lookup_age,table_with_qx_lx_dx,'age','lx') 
                if lookup_lx is None:
                    probability = 0
                else:
                    probability =  lookup_lx / table_with_qx_lx_dx.lx[0]
                EPV = premium * discount * probability
                
                premiums.append({
                    "time t": i,
                    "amount": premium,
                    "discount": discount,
                    "probability": probability,
                    "EPV": EPV
                })
                
            return pd.DataFrame(premiums)

        calculated_premiums = calculate_premiums()

        #EPV of premiums
        EPV_premiums = round(sum(calculated_premiums.EPV), 2)


        def calculate_other_benefits():
            "function to calculate other benefits"
            
            other_benefits = []
            
            for i in range(term_length):
                time = i + 1
                lookup_age = person_age + i
                lookup_lx = vlookup(lookup_age,table_with_qx_lx_dx,'age','lx') 
                if lookup_lx is None:
                    probability = 0
                    amount = 0
                    discount = 0
                else:
                    probability =  lookup_lx / table_with_qx_lx_dx.lx[0]
                    amount = 0.08 * premium
                    discount = V ** time
                EPV = amount * discount * probability
                
                other_benefits.append({
                    "time t": time,
                    "amount": amount,
                    "discount": discount,
                    "probability": probability,
                    "EPV": EPV
                })
                
            return pd.DataFrame(other_benefits)        

        other_benefits = calculate_other_benefits()

        #EPV of other benefits
        EPV_other_benefits = round(sum(other_benefits.EPV), 2)

        # def equation_of_value(EPV_benefits, EPV_expenses, EPV_commission, EPV_other_benefits, EPV_premiums):
        #     "function to calculate the equation of value"
        #     return float((EPV_benefits + EPV_expenses + EPV_commission + EPV_other_benefits) - EPV_premiums)
        
        # goal = 0
        # x0 = premium

        unit_fund_growth_rate = float(assumptions_df[assumptions_df.criteria == 'unit fund growth rate'].value)
        nonunit_fund_growth_rate = float(assumptions_df[assumptions_df.criteria == 'non-unit fund growth rate'].value)
        risk_discount_rate = float(assumptions_df[assumptions_df.criteria == 'risk discount rate'].value)
        mgt_charge = float(assumptions_df[assumptions_df.criteria == 'mgt charge'].value)
        bid_offer_spread = float(assumptions_df[assumptions_df.criteria == 'bid-offer spread'].value)


        def calculate_unit_fund():
            "function to calculate unit fund"
            
            unit_fund = []
            
            for i in range(term_length):
                year = i + 1
                premium_allocated = 0.85 * premium
                cost_of_allocation = premium_allocated * (1 - bid_offer_spread)
                
                if i == 0:
                    fund_after_allocation = cost_of_allocation
                else:
                    fund_after_allocation = unit_fund[i-1]['fund at year end'] + cost_of_allocation
                                                        
                fund_before_mgt_charge = fund_after_allocation * (1 + unit_fund_growth_rate)
                management_charge = fund_before_mgt_charge * mgt_charge
                fund_at_year_end = fund_before_mgt_charge - management_charge
                                                        
                unit_fund.append({
                    'year': year,
                    'premium received': premium,
                    'premium allocated': premium_allocated,
                    'cost of allocation': cost_of_allocation,
                    'fund after allocation': fund_after_allocation,
                    'fund before mgt charge': fund_before_mgt_charge,
                    'mgt charge': management_charge,
                    'fund at year end': fund_at_year_end
                })
            
            return pd.DataFrame(unit_fund)

        unit_fund = calculate_unit_fund()


        def calculate_non_unit_fund():
            "function to calculate non unit fund"
            
            non_unit_fund = []
            inflation_rate = float(assumptions_df[assumptions_df.criteria == 'inflation rate'].value)
            
            for i in range(term_length):
                year = i + 1
                premium_less_cost_of_allocation = unit_fund['premium received'][i] - unit_fund['cost of allocation'][i]
                if (year == 1):
                    expenses = -0.4 * unit_fund['premium received'][i]
                elif (year == 2):
                    expenses = -0.05 * unit_fund['premium received'][i]
                elif (year == 3):
                    expenses = -0.05 * unit_fund['premium received'][i] * (1 + inflation_rate)
                else:
                    expenses = non_unit_fund[i-1]['expenses'] * (1 + inflation_rate)
                
                interest = (premium_less_cost_of_allocation + expenses) * nonunit_fund_growth_rate
                extra_death_cost = -((sum_assured - unit_fund['fund at year end'][i]) * decrements_table.aqxd[i])
                mgt_charge = unit_fund['mgt charge'][i]
                profit = premium_less_cost_of_allocation + expenses + interest + extra_death_cost + mgt_charge
                
                non_unit_fund.append({
                    'year': year,
                    'premium less cost of allocation': premium_less_cost_of_allocation,
                    'expenses': expenses,
                    'interest': interest,
                    'extra death cost': extra_death_cost,
                    'mgt charge': mgt_charge,
                    'profit': profit        
                })
                
            return pd.DataFrame(non_unit_fund)

        non_unit_fund = calculate_non_unit_fund()


        def calculate_pv_profit():
            "function to calculate the present value of profit"
            
            pv_profit = []
            
            for i in range(term_length):
                year = i + 1
                profit_in_year_t = non_unit_fund['profit'][i]
                t_1apx = decrements_table.t_1apx[i]
                profit_signature = profit_in_year_t * t_1apx
                discount_factor = 1/((1+risk_discount_rate)**year)
                discounted_profit = profit_signature * discount_factor
                
                pv_profit.append({
                    'year': year,
                    'profit in year t': profit_in_year_t,
                    't-1(ap)x': t_1apx,
                    'profit signature': profit_signature,
                    'discount factor': discount_factor,
                    'discounted profit': discounted_profit
                })
                
            return pd.DataFrame(pv_profit)

        pv_profit = calculate_pv_profit()

        sum_pv_profit = sum(pv_profit['discounted profit'])


        def calculate_pv_premiums():
            "function to calculate present value of premiums"
            
            pv_premiums = []
            
            for i in range(term_length):
                year = i + 1
                t_1apx = decrements_table.t_1apx[i]
                discount_factor_v = 1/((1+risk_discount_rate)**(year-1))
                discounted_premium = premium * t_1apx * discount_factor_v
                
                pv_premiums.append({
                    'year': year,
                    'premium': premium,
                    't-1(ap)x': t_1apx,
                    'discount factor v^(t-1)': discount_factor_v,
                    'discounted premium': discounted_premium
                })
                
            return pd.DataFrame(pv_premiums)        

        pv_premiums = calculate_pv_premiums()

        sum_pv_premiums = sum(pv_premiums['discounted premium'])

        premium_rate = round((premium/sum_assured) * 100, 3)
        profit_margin = round((sum_pv_profit/sum_pv_premiums) * 100, 2)
        profit_margins.append(profit_margin)
        premium_rates.append(premium_rate)
        ages.append(person_age)

        # print("Premium Rate:: ", premium_rate, "%")
        # print("Premium: ", premium)
        #print(person_age, " | ",profit_margin,"%")

        person_age = person_age + 1
        
        premium = premium + random.randrange(500, 1000, 100)

    #profit_margins.reverse()
    profit_margin_table.columns.insert(1,profit_margins,header=str(term_length))
    premium_rate_table.columns.insert(1,premium_rates, header=str(term_length))
    profit_margins = []
    premium_rates = []
    person_age = 25     
    term_length = term_length - 1

profit_margin_table.to_csv("profit_margins_table.csv")
premium_rate_table.to_csv("premium_rates_table.csv")

print("\n\n\n")
print("                     $$$$$$$$ PROFIT MARGINS $$$$$$$$")
print("________________________________________________________________________________")
print(" Age     |   Profit Margin")
print(profit_margin_table)
print("\n\n\n")

print("                     ######## PREMIUM RATES ##########")
print("________________________________________________________________________________")
print(" Age     |                   Premium Rates")
print(premium_rate_table)