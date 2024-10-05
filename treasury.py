import psycopg2
import simplejson as json
from psycopg2.extras import RealDictCursor
from config import config

def get_treasury_withdrawals_from_database():
    ret = ""
    conn = None
    try:
        params = config('mainnet.ini')
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """ SELECT SUM(treasury_withdrawal.amount) AS amount, stake_address.view as label FROM gov_action_proposal
                    INNER JOIN voting_anchor ON voting_anchor.id = gov_action_proposal.voting_anchor_id
                    INNER JOIN treasury_withdrawal ON gov_action_proposal.id = treasury_withdrawal.gov_action_proposal_id 
                    INNER JOIN stake_address ON stake_address.id = treasury_withdrawal.stake_address_id
                    WHERE gov_action_proposal."type" = 'TreasuryWithdrawals'
                    GROUP BY stake_address.view
                    ORDER BY amount DESC; """ 
        cursor.execute(query)
        ret = json.dumps(cursor.fetchall())
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return str(error)
    finally:
        if conn is not None:
            conn.close()

    return ret

def get_treasury_withdrawal_details_from_database(address):
    ret = ""
    conn = None
    try:
        params = config('mainnet.ini')
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """ SELECT treasury_withdrawal.amount, gov_action_proposal.id as label
                    FROM gov_action_proposal
                    INNER JOIN voting_anchor ON voting_anchor.id = gov_action_proposal.voting_anchor_id
                    INNER JOIN treasury_withdrawal ON gov_action_proposal.id = treasury_withdrawal.gov_action_proposal_id 
                    INNER JOIN stake_address ON stake_address.id = treasury_withdrawal.stake_address_id
                    WHERE gov_action_proposal."type" = 'TreasuryWithdrawals'
                    AND stake_address.view = '"""  + address + "'" 
        cursor.execute(query)
        ret = json.dumps(cursor.fetchall())
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return str(error)
    finally:
        if conn is not None:
            conn.close()

    return ret

def get_votes_for_gov_action_from_database(id):
    ret = ""
    conn = None
    try:
        params = config('mainnet.ini')
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """ SELECT voting_procedure.drep_voter, voting_procedure.vote
                    FROM gov_action_proposal
                    INNER JOIN voting_procedure ON voting_procedure.gov_action_proposal_id = gov_action_proposal.id
                    WHERE gov_action_proposal."type" = 'TreasuryWithdrawals'
                    AND voting_procedure.voter_role = 'DRep'
                    AND gov_action_proposal.id = """  + str(id)  
        cursor.execute(query)
        ret = json.dumps(cursor.fetchall())
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return str(error)
    finally:
        if conn is not None:
            conn.close()

    return ret

def get_reserves_from_database():
    ret = ""
    conn = None
    try:
        params = config('sancho.ini')
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """ SELECT epoch_no, reserves FROM ada_pots ORDER BY epoch_no; """  
        cursor.execute(query)
        ret = json.dumps(cursor.fetchall())
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return str(error)
    finally:
        if conn is not None:
            conn.close()

    return ret

def get_pots_from_database():
    ret = ""
    conn = None
    try:
        params = config('sancho.ini')
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """ SELECT * FROM ada_pots ORDER BY epoch_no; """  
        cursor.execute(query)
        ret = json.dumps(cursor.fetchall())
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return str(error)
    finally:
        if conn is not None:
            conn.close()

    return ret
