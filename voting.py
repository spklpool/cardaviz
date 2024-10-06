import psycopg2
import simplejson as json
from psycopg2.extras import RealDictCursor
from config import config

def return_database_query_as_json(query):
    ret = ""
    conn = None
    try:
        params = config('mainnet.ini')
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        ret = cursor.fetchall()
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return str(error)
    finally:
        if conn is not None:
            conn.close()
    return ret
    

def get_gov_action_proposals_from_database():
        query = """ SELECT gov_action_proposal.id, block.epoch_no, gov_action_proposal.expiration, gov_action_proposal.ratified_epoch, gov_action_proposal.enacted_epoch, 
                           gov_action_proposal.dropped_epoch, gov_action_proposal.expired_epoch
                    FROM gov_action_proposal
                    INNER JOIN tx ON tx.id = gov_action_proposal.tx_id
                    INNER JOIN block ON block.id = tx.block_id; """
        return return_database_query_as_json(query)


def get_gov_action_proposal_details_from_database(proposal_id):
        query = """ SELECT gov_action_proposal.id, block.epoch_no, gov_action_proposal.expiration, gov_action_proposal.ratified_epoch, gov_action_proposal.enacted_epoch, 
                           gov_action_proposal.dropped_epoch, gov_action_proposal.expired_epoch, off_chain_vote_gov_action_data.title, off_chain_vote_gov_action_data.abstract,
                           off_chain_vote_gov_action_data.motivation, off_chain_vote_gov_action_data.rationale
                    FROM gov_action_proposal
                    INNER JOIN voting_anchor ON voting_anchor.id = gov_action_proposal.voting_anchor_id
                    INNER JOIN off_chain_vote_data ON off_chain_vote_data.voting_anchor_id = gov_action_proposal.voting_anchor_id
                    INNER JOIN off_chain_vote_gov_action_data ON off_chain_vote_gov_action_data.off_chain_vote_data_id =  off_chain_vote_data.id
                    INNER JOIN tx ON tx.id = gov_action_proposal.tx_id
                    INNER JOIN block ON block.id = tx.block_id 
                    WHERE gov_action_proposal.id = """ + proposal_id
        return return_database_query_as_json(query)


def get_drep_votes_from_database(drep_id):
    query = """ SELECT voting_procedure.vote, voting_procedure.gov_action_proposal_id 
                FROM voting_procedure
                INNER JOIN drep_hash ON drep_hash.id = voting_procedure.drep_voter
                WHERE drep_voter is NOT NULL
                AND drep_hash.view =  '"""  + drep_id + "'"
    return return_database_query_as_json(query)


def get_pool_votes_from_database(pool_id, proposal_id):
    query = """ SELECT voting_procedure.vote, voting_procedure.gov_action_proposal_id 
                FROM voting_procedure
                INNER JOIN pool_hash ON pool_hash.id = voting_procedure.pool_voter
                INNER JOIN gov_action_proposal ON gov_action_proposal.id = voting_procedure.gov_action_proposal_id
                WHERE pool_voter is NOT NULL
                AND pool_hash.view =  '"""  + pool_id + "'" + " AND gov_action_proposal.id = " + proposal_id
    return return_database_query_as_json(query)


def get_vote_timeline_for_pool(pool_id):
    proposals = get_gov_action_proposals_from_database()
    for proposal in proposals:
        vote_details = get_pool_votes_from_database(pool_id, str(proposal['id']))
        if len(vote_details) > 0:
            proposal['vote'] = vote_details[0]['vote']
        proposal_details = get_gov_action_proposal_details_from_database(str(proposal['id']))
        if len(proposal_details) > 0:
            proposal['title'] = proposal_details[0]['title']
    return json.dumps(proposals)
