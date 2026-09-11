import json
import unittest
from fastapi.testclient import TestClient
from stockanalysis.frontend.api_server import create_app
from stockanalysis.frontend.runtime_policy import FrontendRuntimePolicy
from stockanalysis.frontend.api_adapter import resolve_frontend_response, FrontendApiAdapterError
from stockanalysis.frontend.recommendation_outcomes import API_PATH, OutcomeRequest, parse_outcome_request, resolve_recommendation_outcomes
from stockanalysis.frontend.recommendation_eval_history import EvaluationHistoryError


def payload():
    return {'through':'0','rows':[],'benchmarks':[], 'summary':{'measurement_count':0,'recommendation_count':0,'symbol_count':0,'missing_alpha_count':0,'first_recommendation_date':None,'last_recommendation_date':None}}


class Executor:
    def __init__(self, data=None, error=None):self.data=data or payload();self.error=error;self.queries=[]
    def execute_scalar(self,sql):
        self.queries.append(sql)
        if self.error:raise RuntimeError(self.error)
        return json.dumps(self.data)


class OutcomeExplorerTests(unittest.TestCase):
    def test_filter_normalization_and_cursor(self):
        request=parse_outcome_request(API_PATH+'?symbol=aapl&from_date=2026-05-21&to_date=2026-08-11&horizon=30&benchmark=SPY&alpha=zero&before=2026-09-10:123&through=200&limit=25')
        self.assertEqual(request.symbol,'AAPL');self.assertEqual(request.limit,25)
        self.assertEqual(request.before,'2026-09-10:123')
        self.assertEqual(parse_outcome_request(API_PATH),OutcomeRequest())

    def test_invalid_request_is_rejected_before_sql(self):
        for query in ['symbol=AAPL&symbol=SPY','symbol=AAPL%27','from_date=2026-02-30','from_date=2026-08-01&to_date=2026-07-01','limit=0','limit=101','before=2026-09-10:01','before=2026-09-10:9223372036854775808','through=-1','horizon=31','alpha=outperform','unknown=1','symbol=%00','symbol=%FF']:
            with self.subTest(query=query):
                executor=Executor()
                with self.assertRaises(FrontendApiAdapterError) as caught:resolve_frontend_response(API_PATH+'?'+query,source='live',executor=executor)
                self.assertEqual(caught.exception.code,'FrontendPaginationInvalid');self.assertEqual(executor.queries,[])

    def test_empty_read_is_not_failure_and_failed_read_is_not_empty(self):
        result=resolve_recommendation_outcomes(API_PATH,source='live',executor=Executor())
        self.assertEqual(result['summary']['measurement_count'],0);self.assertEqual(result['rows'],[])
        self.assertFalse(result['pagination']['has_more'])
        for kwargs in [{'executor':Executor(error='postgresql://secret password')},{'source':'fixture','executor':Executor()}]:
            with self.assertRaises(EvaluationHistoryError) as caught:resolve_recommendation_outcomes(API_PATH,**({'source':'live'}|kwargs))
            self.assertNotIn('password',str(caught.exception))

    def test_bad_page_does_not_become_a_valid_report(self):
        data=payload();data['rows']=[{'outcome_id':'1','recommendation_id':'1','measurement_end_date':'2026-09-10'}]
        with self.assertRaises(EvaluationHistoryError):resolve_recommendation_outcomes(API_PATH,source='live',executor=Executor(data))

    def test_auth_and_write_boundaries(self):
        executor=Executor();policy=FrontendRuntimePolicy(profile='local',source='live',auth_mode='read-token',read_token='test-read-only')
        with TestClient(create_app(runtime_policy=policy,executor=executor,observability_mode='disabled')) as client:
            self.assertEqual(client.get(API_PATH).status_code,401);self.assertEqual(executor.queries,[])
            for method in ['POST','PATCH','PUT','DELETE']:
                self.assertEqual(client.request(method,API_PATH,headers={'Authorization':'Bearer test-read-only'}).status_code,405)
            self.assertEqual(executor.queries,[])
            result=client.get(API_PATH,headers={'Authorization':'Bearer test-read-only'})
            self.assertEqual(result.status_code,200);self.assertEqual(result.headers['cache-control'],'no-store')
            self.assertTrue(result.json()['read_only'])


if __name__=='__main__':unittest.main()
