"""Synthetic logic tests plus exact checks against the original ECB public file."""
from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from space_cx.analysis import GROUPS,prepare,estimate,CSV_NAME

def fixture():
    rows=[]
    for i,w in enumerate([1,3,2,5]):
        r={c:0 for cols in GROUPS.values() for c in cols}
        r.update(ID=i+1,COUNTRY='PT',AGE=1,D1=1,ROUND=1,FIELD=1,
                 Gross_weight=w,QQ3=999999,QB8=np.nan)
        rows.append(r)
    rows[0].update(QA10_1=1,QA10_2=1,QA9_1=1,QQ3=2,QB7_1=1)
    rows[1].update(QA10_4=1,QA9_4=1,QQ3=1,QB7_3=1)
    rows[3].update(QA9_5=1,**{c:np.nan for c in GROUPS['pos']})
    return pd.DataFrame(rows)

class SurveyLogic(unittest.TestCase):
    def test_weighted_share_and_multiple_answers(self):
        d=prepare(fixture());m=estimate(d,'pos_any')
        self.assertEqual(m['n'],2)
        self.assertEqual(m['n_positive'],1)
        self.assertAlmostEqual(m['percent'],25)
        self.assertAlmostEqual(estimate(d,'pos_any',False)['percent'],50)
    def test_unknown_and_skip_are_not_negative_answers(self):
        d=prepare(fixture())
        self.assertTrue(pd.isna(d.loc[2,'pos_any']))
        self.assertTrue(pd.isna(d.loc[3,'pos_any']))
        self.assertFalse(d.loc[1,'pos_any'])
        self.assertFalse(d.loc[3,'valid_acceptance'])
        self.assertFalse(d.loc[2,'valid_preference'])
    def test_weight_scale_invariance(self):
        r=fixture();a=estimate(prepare(r),'online_any')
        r.Gross_weight=r.Gross_weight*1000
        b=estimate(prepare(r),'online_any')
        self.assertAlmostEqual(a['percent'],b['percent'])
        self.assertAlmostEqual(a['effective_n_kish'],b['effective_n_kish'])
    def test_empty_group(self):
        d=prepare(fixture());self.assertIsNone(estimate(d.iloc[0:0],'pos_any')['percent'])
    def test_bad_weights_and_duplicate_ids_fail(self):
        r=fixture();r.loc[0,'Gross_weight']=0
        with self.assertRaises(ValueError):prepare(r)
        r=fixture();r.loc[1,'ID']=r.loc[0,'ID']
        with self.assertRaises(ValueError):prepare(r)
    def test_unexpected_binary_code_fails(self):
        r=fixture();r.loc[0,'QA10_1']=6
        with self.assertRaises(ValueError):prepare(r)

class SourceRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=ROOT/'data'/'raw'/CSV_NAME
        if not p.exists():raise unittest.SkipTest('Run scripts/download_data.py for source regression checks.')
        cls.df=prepare(pd.read_csv(p))
    def test_source_counts_and_headlines(self):
        d=self.df
        self.assertEqual(len(d),40981);self.assertEqual(d.COUNTRY.nunique(),18)
        expected={'pos_any':(39404,23.240211),'accept_any':(38719,23.574549),
                  'online_any':(13884,18.012594),'cashless_preference':(40795,57.581951)}
        for key,(n,p) in expected.items():
            m=estimate(d,key);self.assertEqual(m['n'],n)
            self.assertAlmostEqual(m['percent'],p,places=5)
    def test_preference_partition_and_country_weight_reconciliation(self):
        d=self.df
        self.assertAlmostEqual(sum(estimate(d,k)['percent'] for k in
            ['cashless_preference','cash_preference','no_preference']),100)
        valid=d.loc[d.valid_pos]
        numerator=sum(g.loc[g.pos_any,'Gross_weight'].sum() for _,g in valid.groupby('COUNTRY'))
        self.assertAlmostEqual(100*numerator/valid.Gross_weight.sum(),estimate(d,'pos_any')['percent'])

if __name__=='__main__':unittest.main()
