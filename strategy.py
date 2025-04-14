
from outcomes import Outcomes


# Strategy: Impose Tariffs
# Description: Add import taxes on certain goods or sectors
def impose_tariffs():
    return Outcomes({
        "GDP_change": -2.5,
        "Political_boost_loss": 3,
        "Trade_balance_shift": -150,
    })
     

# Strategy: Retaliate Tariffs
# Description: Respond with equal tariffs to a partner's initial move
def retaliate_tariffs():
    return Outcomes({
        "GDP_change": -3.0,
        "Political_boost_loss": 1,
        "Trade_balance_shift": 100,
    })

# Strategy: Subsidize Exports
# Description: Provide financial support to domestic exporters
def subsidize_exports():
    return Outcomes({
        "GDP_change": 1.0,
        "Political_boost_loss": -5,
        "Trade_balance_shift": 100,
    })

# Strategy: Currency Devaluation
# Description: Lower currency value to make exports more competitive
def currency_devaluation():
    return Outcomes({
        "GDP_change": 3.0,
        "Political_boost_loss": 1,
        "Trade_balance_shift": -100,
    })

# Strategy: File WTO Complaint
# Description: Use institutional rules to resolve trade disputes
def file_wto_complaint():
    return Outcomes({
        "GDP_change": 0.5,
        "Political_boost_loss": -10,
        "Trade_balance_shift": 50,
    })

# Strategy: Negotiate Bilateral Deal
# Description: Engage diplomatically to reduce tensions and reach concessions
def negotiate_bilateral_deal():
    return Outcomes({
        "GDP_change": 0.5,
        "Political_boost_loss": -10,
        "Trade_balance_shift": -50,
    })

# Strategy: Engage in Multilateral Talks
# Description: Bring in allies to create global pressure on opponent
def engage_in_multilateral_talks():
    return Outcomes({
        "GDP_change": 0.5,
        "Political_boost_loss": -10,
        "Trade_balance_shift": -50,
    })

# Strategy: Block Imports on Security Grounds
# Description: Use national security as a justification (e.g., rare earths)
def block_imports_on_security_grounds():
    return Outcomes({
        "GDP_change": 0.5,
        "Political_boost_loss": -10,
        "Trade_balance_shift": -50,
    })

# Strategy: Delay Trade Approvals
# Description: Use bureaucracy and inspections to slow trade flow
def delay_trade_approvals():
    return Outcomes({
        "GDP_change": 0.5,
        "Political_boost_loss": -10,
        "Trade_balance_shift": -50,
    })

# Strategy: Impose Sanctions
# Description: Use trade as a tool to punish geopolitical actions
def impose_sanctions():
    return Outcomes({
        "GDP_change": 0.5,
        "Political_boost_loss": -10,
        "Trade_balance_shift": -50,
    })

# Strategy: Form Trade Alliance
# Description: Strengthen partnerships to isolate opponent economically
def form_trade_alliance():
    return Outcomes({
        "GDP_change": 0.5,
        "Political_boost_loss": -10,
        "Trade_balance_shift": -50,
    })

# Strategy: Public Campaigning
# Description: Frame the opponent’s action to gain domestic/popular support
def public_campaigning():
    return Outcomes({
        "GDP_change": 0.5,
        "Political_boost_loss": -10,
        "Trade_balance_shift": -50,
    })

# Strategy: Mirror Opponent's Move
# Description: Tit-for-tat (e.g., same level of tariff or restriction)
def mirror_opponents_move():
    pass

# Strategy: Offer Selective Concessions
# Description: Cooperate partially (on agriculture, tech, etc.)
def offer_selective_concessions():
    pass


def wait_and_see():
    return Outcomes({
        "GDP_change": 0.0001,
        "Political_boost_loss": 0.001,
        "Trade_balance_shift": 0.001,
    }
    )
  