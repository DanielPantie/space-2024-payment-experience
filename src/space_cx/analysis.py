"""Explicit survey bases and weighted descriptive estimates.

The public-use file is wide, one row per respondent. No special response code
is interpreted as a real numeric value or as a negative survey answer.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

SOURCE_URL = 'https://www.ecb.europa.eu/stats/ecb_surveys/space/shared/pdf/2024_SPACE_microdata.en.zip'
CSV_NAME = 'SPACE Public Use File.csv'
CSV_SHA256 = '0031ba01493a3e800907adaf83a9d457f9f1bd1cfc2e8ff3842e69ed8ba28b99'
COUNTRIES = {'AT':'Austria','BE':'Belgium','CY':'Cyprus','EE':'Estonia','ES':'Spain',
             'FI':'Finland','FR':'France','GR':'Greece','HR':'Croatia','IE':'Ireland',
             'IT':'Italy','LT':'Lithuania','LU':'Luxembourg','LV':'Latvia','MT':'Malta',
             'PT':'Portugal','SI':'Slovenia','SK':'Slovakia'}
GROUPS = {
    'acceptance': [f'QA9_{i}' for i in range(1,6)],
    'pos': [f'QA10_{i}' for i in range(1,5)],
    'online': ['QB7_1'] + [f'QB7_{i}' for i in range(21,27)] + ['QB7_3'],
    'adoption': [f'QQ18_{i}' for i in range(1,11)],
    'privacy': [f'QQ16_{i}' for i in range(1,5)],
}

@dataclass(frozen=True)
class Metric:
    label: str
    base: str
    positive: str | tuple[str, ...]
    period: str
    kind: str = 'binary'
    value: int = 1

METRICS = {
    'pos_any': Metric('Any in-store technical problem','valid_pos',tuple(GROUPS['pos'][:3]),'Past month'),
    'accept_any': Metric('Preferred method unavailable or restricted','valid_acceptance',tuple(GROUPS['acceptance'][:3]),'Past month'),
    'online_any': Metric('Any online payment difficulty','valid_online',tuple(GROUPS['online'][:-1]),'Diary day'),
    'cashless_preference': Metric('Prefer cashless payments','valid_preference','QQ3','General preference','category',2),
    'cash_preference': Metric('Prefer cash','valid_preference','QQ3','General preference','category',1),
    'no_preference': Metric('No clear payment preference','valid_preference','QQ3','General preference','category',3),
    'privacy_any': Metric('Any privacy concern','valid_privacy',('QQ16_1','QQ16_2'),'General attitude'),
}
for i, label in enumerate(['Cash not accepted','Card/mobile not accepted','Card/mobile minimum amount'],1):
    METRICS[f'accept_{i}'] = Metric(label,'valid_acceptance',f'QA9_{i}','Past month')
for i, label in enumerate(['Card payment problem','Mobile payment problem','Cash self-checkout problem'],1):
    METRICS[f'pos_{i}'] = Metric(label,'valid_pos',f'QA10_{i}','Past month')
for col,label in zip(GROUPS['online'][:-1],['Entering payment details','Late one-time password',
    'Banking app redirect failed','Authentication details unavailable','Biometrics did not work',
    'Authentication details rejected','Had to download an app']):
    METRICS[col] = Metric(label,'valid_online',col,'Diary day')
for i,label in enumerate(['Easier to use','Cheaper','Higher security','More privacy','Innovative functions',
    'Faster to use','Incentives or loyalty','Friends/family recommendation','Works offline','Not interested'],1):
    METRICS[f'adopt_{i}'] = Metric(label,'valid_adoption',f'QQ18_{i}','Stated adoption factor')
for i,label in enumerate(['Credentials only','Credentials plus extra verification','Biometrics'],1):
    METRICS[f'auth_{i}'] = Metric(label,'valid_auth','QB8','Authentication preference','category',i)
for i,label in enumerate(['Want more private transactions','Concerned about use of data'],1):
    METRICS[f'privacy_{i}'] = Metric(label,'valid_privacy',f'QQ16_{i}','General attitude')

def selected(df: pd.DataFrame, cols: list[str] | tuple[str,...]) -> pd.Series:
    """At least one explicit selection, without converting missing to 'No'."""
    return df[list(cols)].eq(1).any(axis=1)

def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    """Keep original fields intact and add auditable derived columns."""
    df = raw.drop(columns=['Unnamed: 0'], errors='ignore').copy()
    if not df.ID.is_unique:
        raise ValueError('Respondent IDs are not unique; investigate before analysis.')
    if df.Gross_weight.isna().any() or not df.Gross_weight.gt(0).all():
        raise ValueError('Weights must be nonmissing and positive.')
    if not set(df.COUNTRY).issubset(COUNTRIES):
        raise ValueError('Unexpected country coverage; review source edition.')
    for cols in GROUPS.values():
        unexpected = (df[cols].notna() & ~df[cols].isin([0,1])).any(axis=1)
        if unexpected.any():
            raise ValueError('Unexpected multi-select coding; inspect raw input.')
    df['country_name'] = df.COUNTRY.map(COUNTRIES)
    age = pd.Series(pd.NA,index=df.index,dtype='string')
    age.loc[df.AGE.between(1,3)] = '18-34'
    age.loc[df.AGE.between(4,7)] = '35-54'
    age.loc[df.AGE.between(8,12)] = '55+'
    df['age_group'] = age
    df['gender'] = df.D1.map({1:'Male',2:'Female',3:'Other / non-binary'})
    df['survey_mode'] = df.FIELD.map({1:'Telephone',2:'Web'})
    df['round_label'] = df.ROUND.map({1:'Sep-Nov 2023',2:'Apr-Jun 2024'})
    df['valid_acceptance'] = selected(df,GROUPS['acceptance'][:4]) & df.QA9_5.ne(1)
    df['valid_pos'] = selected(df,GROUPS['pos']) & df.QA9_5.ne(1)
    df['valid_online'] = selected(df,GROUPS['online'])
    df['valid_preference'] = df.QQ3.isin([1,2,3])
    df['valid_auth'] = df.QB8.isin([1,2,3])
    df['valid_adoption'] = selected(df,GROUPS['adoption'])
    df['valid_privacy'] = selected(df,GROUPS['privacy'][:3]) & df.QQ16_4.ne(1)
    for key,metric in METRICS.items():
        positive = (selected(df,metric.positive) if isinstance(metric.positive,tuple)
                    else df[metric.positive].eq(metric.value))
        # NA marks unknown or out-of-scope. It remains distinct from False.
        df[key] = positive.astype('boolean').where(df[metric.base],pd.NA)
    return df

def estimate(df: pd.DataFrame,key: str,weighted: bool=True) -> dict:
    metric = METRICS[key]
    valid = df[metric.base]
    d = df.loc[valid]
    w = d.Gross_weight.to_numpy(float) if weighted else np.ones(len(d))
    y = d[key].astype(float).to_numpy()
    denom = float(w.sum())
    return {'metric':key,'label':metric.label,'period':metric.period,'base':metric.base,
            'n':len(d),'n_positive':int(y.sum()),
            'percent':float(100*np.dot(w,y)/denom) if denom else None,
            'effective_n_kish':float(denom**2/np.dot(w,w)) if denom else None,
            'weighted':weighted}

def summarize(df: pd.DataFrame,keys=None,weighted=True) -> pd.DataFrame:
    return pd.DataFrame([estimate(df,k,weighted) for k in (keys or METRICS)])

def by_group(df: pd.DataFrame,column:str,keys:list[str]) -> pd.DataFrame:
    out=[]
    for group,d in df.groupby(column,observed=True,dropna=True):
        for key in keys:
            out.append({'group_column':column,'group':group,**estimate(d,key)})
    return pd.DataFrame(out)

def standardized_age(df: pd.DataFrame,key:str) -> pd.DataFrame:
    """Fix country mix to the overall valid base for descriptive age comparison.

    Standardization changes the comparison population, not the design weights.
    It does not adjust for use intensity, income, survey mode or other confounders.
    """
    base=df.loc[df[METRICS[key].base]]
    country_weights=base.groupby('COUNTRY').Gross_weight.sum()
    country_weights=country_weights/country_weights.sum()
    out=[]
    for age,d in base.groupby('age_group',observed=True):
        rates={c:estimate(g,key)['percent'] for c,g in d.groupby('COUNTRY')}
        if set(rates)!=set(country_weights.index):
            raise ValueError('Cannot standardize over missing age-country cells.')
        out.append({'metric':key,'age_group':age,'n':len(d),
            'unadjusted_percent':estimate(d,key)['percent'],
            'country_standardized_percent':sum(country_weights[c]*rates[c] for c in rates)})
    return pd.DataFrame(out)

def audit(raw:pd.DataFrame,df:pd.DataFrame,path:Path) -> dict:
    multiselect={}
    for name,cols in GROUPS.items():
        a=raw[cols].eq(1)
        multiselect[name]={'selected_any_n':int(a.any(axis=1).sum()),
            'all_zero_n':int(raw[cols].eq(0).all(axis=1).sum()),
            'all_missing_n':int(raw[cols].isna().all(axis=1).sum()),
            'exclusive_last_option_conflicts_n':int((a.iloc[:,-1]&a.iloc[:,:-1].any(axis=1)).sum())}
    # QA9_4, not QA9_5, is the exclusive 'always available' response.
    multiselect['acceptance']['always_with_barrier_conflicts_n']=int((raw.QA9_4.eq(1)&selected(raw,GROUPS['acceptance'][:3])).sum())
    multiselect['adoption']['above_three_selections_n']=int(raw[GROUPS['adoption']].eq(1).sum(axis=1).gt(3).sum())
    return {'rows':len(raw),'raw_columns':len(raw.columns),'unique_respondents':int(raw.ID.nunique()),
        'duplicate_ids':int(raw.ID.duplicated().sum()),'exact_duplicate_rows':int(raw.duplicated().sum()),
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'expected_sha256':CSV_SHA256,'countries':raw.COUNTRY.value_counts().to_dict(),
        'weight_missing_n':int(raw.Gross_weight.isna().sum()),
        'weight_nonpositive_n':int(raw.Gross_weight.le(0).sum()),
        'weight_summary':raw.Gross_weight.describe().to_dict(),
        'question_response_audit':multiselect,
        'valid_bases':{c:int(df[c].sum()) for c in df if c.startswith('valid_')},
        'online_selected_but_not_diary_online_n':int((df.valid_online&raw.Q1_7.ne(1)).sum())}

def denominator_sensitivity(df:pd.DataFrame) -> pd.DataFrame:
    """Contrast valid-base estimates with positive-report shares of eligible records.

    The alternative is NOT a problem-rate estimate: unknowns remain in its
    denominator. It illustrates how base decisions affect reported percentages.
    """
    out=[]
    for key,eligible in [('pos_any',df.QA9_5.ne(1)),('accept_any',df.QA9_5.ne(1)),
                         ('online_any',df.Q1_7.eq(1))]:
        pos=df[key].fillna(False)
        m=estimate(df,key)
        alt=100*df.loc[eligible&pos,'Gross_weight'].sum()/df.loc[eligible,'Gross_weight'].sum()
        out.append({'metric':key,'valid_n':m['n'],'eligible_n':int(eligible.sum()),
                    'valid_base_percent':m['percent'],'positive_reports_per_eligible_records_percent':float(alt),
                    'interpretation':'Alternative retains non-substantive responses in denominator; not an estimated problem rate.'})
    return pd.DataFrame(out)

def write_results(df:pd.DataFrame,raw:pd.DataFrame,path:Path,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    tables={
        'metrics_weighted':summarize(df), 'metrics_unweighted':summarize(df,weighted=False),
        'by_country':by_group(df,'country_name',['pos_any','accept_any','online_any','cashless_preference','privacy_any']),
        'by_age':by_group(df,'age_group',['pos_any','accept_any','online_any','cashless_preference','privacy_any']),
        'by_mode':by_group(df,'survey_mode',['pos_any','accept_any','online_any','cashless_preference']),
        'by_round':by_group(df,'round_label',['pos_any','accept_any','online_any','cashless_preference']),
        'age_standardization':pd.concat([standardized_age(df,k) for k in ['pos_any','cashless_preference']],ignore_index=True),
        'denominator_sensitivity':denominator_sensitivity(df),
    }
    for name,t in tables.items():
        t.to_csv(out/f'{name}.csv',index=False,float_format='%.10f')
    info=audit(raw,df,path)
    (out/'audit.json').write_text(json.dumps(info,indent=2))
    return tables,info
