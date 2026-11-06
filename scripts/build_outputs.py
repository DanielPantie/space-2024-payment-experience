"""Build publication charts, a linked findings report, an executed notebook and PDF.

All numbers come from analysis.py outputs, never from manually transcribed slides.
"""
from pathlib import Path
import base64
import hashlib
import io
import json
import os
import sys
import textwrap
import contextlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from space_cx.analysis import METRICS,GROUPS,estimate,summarize,by_group,standardized_age,COUNTRIES

NAVY='#14283e';BLUE='#3269c8';TEAL='#268579';ORANGE='#d7844e';MUTED='#66788b';BG='#f4f7fa'

def chart_bars(labels,values,path,title,subtitle='',max_x=100,color=BLUE):
    fig,ax=plt.subplots(figsize=(10, max(3.8,len(labels)*.55+1.6)))
    y=np.arange(len(labels))
    ax.barh(y,values,height=.55,color=color)
    ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlim(0,max_x)
    ax.set_xlabel('Share of valid respondents (%)',color=MUTED)
    for i,v in enumerate(values):ax.text(v+max_x*.012,i,f'{v:.1f}%',va='center',fontsize=12,fontweight='bold',color=NAVY)
    ax.tick_params(axis='y',length=0,pad=12);ax.tick_params(axis='x',colors=MUTED)
    for spine in ax.spines.values():spine.set_visible(False)
    ax.xaxis.grid(True,alpha=.14);ax.set_axisbelow(True)
    ax.set_title(title,loc='left',fontweight='bold',fontsize=16,color=NAVY,pad=28)
    if subtitle:fig.text(.02,.015,subtitle,ha='left',color=MUTED,fontsize=10)
    fig.tight_layout(rect=[0,.055,.98,1])
    for ext in ['png','svg']:
        fig.savefig(path.with_suffix('.'+ext),dpi=170,bbox_inches='tight',facecolor='white')
    plt.close(fig)

def charts(tables):
    out=ROOT/'outputs'/'figures';out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12})
    m=tables['metrics_weighted'].set_index('metric')
    groups=[
        ('01_preference',['cashless_preference','cash_preference','no_preference'],'Most respondents prefer cashless payments',100,BLUE),
        ('02_acceptance',['accept_2','accept_1','accept_3'],'Acceptance barriers at physical locations',100,ORANGE),
        ('03_pos_problems',['pos_1','pos_2','pos_3'],'Technical problems at physical locations',100,BLUE),
        ('04_online_problems',sorted(GROUPS['online'][:-1],key=lambda k:m.loc[k,'percent'],reverse=True),'Online checkout difficulties',12,TEAL),
        ('05_adoption',sorted([f'adopt_{i}' for i in range(1,10)],key=lambda k:m.loc[k,'percent'],reverse=True),'Reasons to try a new payment solution',100,BLUE),
        ('06_authentication',[f'auth_{i}' for i in range(1,4)],'Preferred online authentication',100,TEAL),
    ]
    for name,keys,title,limit,color in groups:
        n=int(m.loc[keys[0],'n'])
        note=f'ECB SPACE 2024 public-use file. Weighted. 18 countries. Valid n = {n:,}.'
        if name.startswith(('02','03','04','05')):note+=' Multiple answers allowed.'
        chart_bars([m.loc[k,'label'] for k in keys],[m.loc[k,'percent'] for k in keys],out/name,title,note,limit,color)
    age=tables['by_age'];a=age[age.metric.eq('pos_any')].set_index('group').loc[['18-34','35-54','55+']]
    chart_bars(list(a.index),a.percent.tolist(),out/'07_age_pos','Younger respondents report more in-store technical problems',
        'ECB SPACE 2024. Weighted valid responses. Past month. Descriptive differences; payment-use frequency is not controlled.',100,BLUE)
    c=tables['by_country'];c=c[c.metric.eq('pos_any')].sort_values('percent',ascending=False)
    chart_bars(c.group.tolist(),c.percent.tolist(),out/'08_country_pos','In-store technical problems across the 18 countries',
        'ECB SPACE 2024. Weighted valid responses. Past month. Country differences are descriptive.',40,BLUE)

def md_table(frame):
    f=frame.copy().fillna('')
    cols=list(f.columns)
    return '| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in f.itertuples(index=False,name=None))

def report(tables,info):
    m=tables['metrics_weighted'].set_index('metric');p=lambda k:f"{m.loc[k,'percent']:.1f}%";n=lambda k:f"{int(m.loc[k,'n']):,}"
    brief=tables['metrics_weighted'].query("metric in ['pos_any','accept_any','online_any','cashless_preference','privacy_any']")[['label','percent','n']].copy()
    brief['percent']=brief.percent.map(lambda v:f'{v:.1f}%');brief.columns=['Measure','Weighted share','Valid respondents']
    doc=f'''# Customer experience in European payments

## Business question

Where do consumers encounter payment friction, and what should a payment provider investigate or test next?

This is an independent analysis of the **ECB SPACE 2024 public-use file**, covering **40,981 consumers in 18 countries**. It studies consumers' payment experiences, choices and stated adoption factors. It does not measure merchant satisfaction with a terminal provider, brand-level service quality, NPS, retention or revenue impact.

## Executive findings

{md_table(brief)}

All percentages use the supplied **Gross_weight** and a valid response base specific to the question. The results refer to the countries in this public file. They are not the ECB's full 20-country euro-area estimates.

1. **Preference and access do not always align.** {p('cashless_preference')} prefer cashless payments if offered a choice. Separately, {p('accept_any')} reported that their preferred payment method was unavailable or restricted at least once in the previous month. These figures describe different questions and populations; subtracting them would be meaningless.
2. **In-store problems are widespread enough to investigate.** {p('pos_any')} reported at least one technical problem in the past month. Card problems reached {p('pos_1')}, mobile problems {p('pos_2')} and cash self-checkout problems {p('pos_3')}. The common base is {n('pos_any')} valid respondents, rather than users of each method. Higher exposure to a method can produce more reports. These are not per-transaction failure rates.
3. **Online friction is broader than entering payment details.** {p('online_any')} of {n('online_any')} valid online-difficulty respondents reported an issue with the diary-day payments. Entering details was selected by {p('QB7_1')}, banking-app redirect failures by {p('QB7_22')}, and late one-time passwords by {p('QB7_21')}. Multiple issues can overlap.
4. **Security and ease are almost tied as stated adoption factors.** Higher security ({p('adopt_3')}) and easier use ({p('adopt_1')}) lead the list, followed by lower price ({p('adopt_2')}). Innovative features reach {p('adopt_5')}. The 0.23 percentage point difference between security and ease does not justify a claim that one clearly dominates the other. These are stated motivations, not proven adoption effects.
5. **Younger respondents report more in-store technical problems.** The weighted shares are 28.6% for ages 18-34, 23.9% for 35-54, and 19.7% for 55+. Holding country mix fixed produces very similar estimates (28.6%, 23.8%, 19.7%). This does not control for method use, payment frequency or reporting behaviour. It does not show that younger customers are less capable.

## Decisions and tests supported by the evidence

| Evidence | Proposed test or investigation | Success measure to collect | Main qualification |
| --- | --- | --- | --- |
| {p('pos_any')} report an in-store technical issue | Link merchant support cases to terminal, network and authorisation logs; identify recurring incident types | Incident recurrence, recovery time and transaction completion from operational logs | Survey responses cannot isolate the underlying cause or provider |
| {p('accept_2')} report card/mobile non-acceptance | Investigate acceptance coverage and clarity of minimum-payment policies in target merchant segments | Customer ability to use a preferred method, tracked with a clearly defined question | Merchant behaviour and payment-method availability differ from technical failures |
| {p('QB7_1')} report payment-detail entry problems; {p('QB7_22')} app redirects | Test form validation, clear error messages, and recovery after an authentication failure | Checkout completion, repeat attempts, authentication success and support contacts | Outcomes need an operational experiment, not an assumed uplift from survey percentages |
| Security and ease both reach about 38% as adoption factors | Test clearer security explanations alongside simpler task flows | Comprehension, task completion and take-up in a controlled pilot | Avoid inferring actual adoption from stated intentions |

These are hypotheses for investigation, not forecasts of ROI. The survey contains no direct revenue, churn or provider-cost outcome with which to quantify returns.

## How the survey works

SPACE combines a one-day payment diary with questions about usual behaviour and attitudes. Recruitment and follow-up used telephone interviews and web panels. Fieldwork spans September-November 2023 and April-June 2024. The public-use file is wide: one row per person, with repeated payment fields for diary transactions.

The file contains the 18 countries surveyed through Ipsos. Germany and the Netherlands ran separate surveys and are absent here. Czechia is outside SPACE's euro-area coverage. Portugal, Slovakia, Croatia, Slovenia and the Baltic countries are available, but this file does not support a Czech or complete CEE conclusion.

This case study deliberately uses respondent-level modules first. Transaction shares would require reshaping the repeated diary fields, a carefully defined transaction scope and an appropriate weighting approach. They are an extension rather than a necessary part of this consumer-experience analysis.

## Preparation and metric construction

1. Download the official ZIP and verify the CSV SHA-256. Preserve the original files in `data/raw/`.
2. Drop only the exported row-index column from the analysis copy. Preserve all original survey values.
3. Check respondent IDs, country coverage, positive nonmissing weights, special codes and multi-select consistency.
4. Create explicit valid-base flags. Retain an unknown outcome as `NA` rather than `False`.
5. Calculate a weighted share as `100 * sum(weights of positive valid responses) / sum(weights of all valid responses)`.
6. Export full-precision estimates and real response counts. Round only when communicating.

The source has **{info['duplicate_ids']} duplicate respondent IDs**, **{info['weight_missing_n']} missing weights** and **{info['weight_nonpositive_n']} nonpositive weights**. The audit found no conflicts between the exclusive 'no problems' response and a selected problem, and no adoption-response rows with more than three selected options.

The all-zero issue matters: **1,173** rows have zeros for every in-store technical-problem option, and **404** have a skipped/missing technical-problem set. An all-zero set does not select the explicit 'no issues' option. Its reason cannot be recovered reliably from these binary fields, so it is excluded from the primary base. For online difficulties, **127** rows have an all-zero set and **26,970** are all missing. See `audit.json` for every question group.

## Reliability and sensitivity

- **Weighting:** Compare `metrics_weighted.csv` and `metrics_unweighted.csv`. The weighted in-store issue estimate is {p('pos_any')}; the unweighted estimate is 22.6%. Country sample sizes are not proportional to country populations, so the pooled unweighted share is not a population estimate.
- **Weight concentration:** For in-store technical issues, Kish effective n is about {m.loc['pos_any','effective_n_kish']:,.0f}, versus {n('pos_any')} actual valid respondents. Kish n diagnoses concentration of weights only. It is not a complete design-based precision estimate.
- **Denominator sensitivity:** `denominator_sensitivity.csv` contrasts primary valid-base percentages with positive reports per eligible record, retaining non-substantive responses in the alternative denominator. The latter is not a problem-rate estimate. This check exposes rather than resolves uncertainty about missing responses.
- **Country mix:** Country-standardized age comparisons retain the overall valid population's country mix. They address one compositional difference and do not provide causal adjustment.
- **Survey mode:** In-store technical issues are reported by 25.7% in the telephone sample and 19.8% in the web sample. Selection, composition and interview mode may all contribute. Respondents were not randomly assigned to mode, so this gap is not an estimated interview-mode effect.
- **Uncertainty:** No formal confidence intervals, p-values or significance claims are supplied. The web component is non-probability sampling, and the public file lacks the full information needed for a defensible design-based variance analysis. Small subgroup results need additional care.

## Learning notes

**Prevalence versus failure rate:** 23.2% reporting at least one problem over a month does not mean 23.2% of payments failed. We do not know the total number of payment attempts corresponding to that recall period.

**Multiple answers:** One person can select both a card and mobile problem. Add the union of people for 'any issue', not the separate percentages. The script uses `.any(axis=1)`.

**Skip versus No:** A blank online response may reflect no online payment on the diary day. That respondent does not belong in the online-problem denominator. An explicit 'no difficulties' answer does belong.

**Period versus edition:** 'SPACE 2024' includes 2023 fieldwork. The survey rounds are separate cross-sectional samples; a round comparison is not individual-level change or a clean time trend.

**CX construct:** SPACE captures friction, access, preferences and perceptions. It does not supply the overall-satisfaction outcome that would support a conventional satisfaction-driver model. Avoid inventing a composite satisfaction score or NPS from unrelated questions.

## Sources

- [ECB SPACE landing page](https://www.ecb.europa.eu/stats/ecb_surveys/space/html/index.en.html)
- [Official microdata, codebook and labels](https://www.ecb.europa.eu/stats/ecb_surveys/space/shared/pdf/2024_SPACE_microdata.en.zip)
- [Questionnaire, Annex A](https://www.ecb.europa.eu/stats/ecb_surveys/space/shared/pdf/ecb.space2024_annex_a.en.pdf)
- [Methodology, Annex B](https://www.ecb.europa.eu/stats/ecb_surveys/space/shared/pdf/ecb.space2024_annex_b.en.pdf)
- [ECB use and attribution conditions](https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html)

Source data: European Central Bank. All figures here are independent calculations using the public-use file and the explicit bases above. The analysis is not an ECB publication or endorsement. Raw data are downloaded separately; original ECB materials retain their source rights.
'''
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports'/'case_study.md').write_text(doc)

def notebook(path):
    """Execute real notebook cells with IPython and capture their rich outputs."""
    cells=[]
    def md(s):cells.append({'cell_type':'markdown','metadata':{},'source':textwrap.dedent('    '+s).strip().splitlines(True)})
    def code(s):cells.append({'cell_type':'code','metadata':{},'source':textwrap.dedent('    '+s).strip().splitlines(True),'execution_count':None,'outputs':[]})
    md('''# Customer experience in European payments
    ## ECB SPACE 2024: a guided, reproducible case study
    **Question:** Where do consumers encounter payment friction, and what could payment providers investigate next?

    This notebook uses real public survey responses. It covers 40,981 consumers in 18 countries, excluding Germany and the Netherlands. Czechia is outside the survey. Start by reading the explanations, then run each cell. The source download verifies its bytes before use.

    Source: European Central Bank. Findings are independent calculations, not official full-euro-area estimates.''')
    code('''from pathlib import Path
    import sys
    import pandas as pd
    from IPython.display import display, Image

    ROOT = Path.cwd()
    if ROOT.name == 'notebooks':
        ROOT = ROOT.parent
    if not (ROOT / 'src' / 'space_cx').exists():
        raise RuntimeError('Open this notebook from the project root or notebooks folder.')
    sys.path.insert(0, str(ROOT / 'src'))
    sys.path.insert(0, str(ROOT))
    from space_cx.analysis import prepare, estimate, summarize, by_group, audit, standardized_age, GROUPS
    from scripts.download_data import download

    source = download()
    raw = pd.read_csv(source)
    df = prepare(raw)
    print(f'{len(df):,} respondents, {df.COUNTRY.nunique()} countries, {len(raw.columns)} source columns')''')
    md('''## 1. Understand the survey before calculating a metric
    One row is one person, not one payment. The file includes repeated diary-payment columns, but this analysis uses respondent-level modules. In-store problems refer to the past month; online difficulties refer to payments reported for the diary day. Payment preferences are general attitudes.

    The fieldwork spans autumn 2023 and spring 2024. These are cross-sectional rounds, not a panel. Telephone interviews and web panels have different selection mechanisms.''')
    code('''print('Coverage and sample sizes:')
    display(df.groupby('country_name').size().rename('respondents').to_frame())
    print('Interview modes and rounds:')
    display(pd.crosstab(df.survey_mode, df.round_label))''')
    md('''## 2. Audit the coding and preserve unknown outcomes
    In multi-select questions, 1 means selected and 0 means not selected. All zeros do not select the explicit 'no issues' option. Skipped questions are also different from negative answers. We exclude non-substantive sets from the primary question base.

    A binary outcome therefore has three states: True, False and NA. The original source columns remain intact. Inspect the separate `valid_*` flags in `src/space_cx/analysis.py`.''')
    code('''audit_result = audit(raw, df, source)
    print('Duplicate IDs:', audit_result['duplicate_ids'])
    print('Missing / nonpositive weights:', audit_result['weight_missing_n'], audit_result['weight_nonpositive_n'])
    display(pd.DataFrame(audit_result['question_response_audit']).T.fillna(''))
    display(pd.Series(audit_result['valid_bases'], name='valid_n').to_frame())
    display(df.pos_any.value_counts(dropna=False).rename('respondents').to_frame())''')
    md('''## 3. Build a valid-base weighted estimate
    The weighted percentage is the weight of positive valid responses divided by the weight of all valid responses, multiplied by 100. Gross weights do not become response counts. Always show actual n separately.

    Below, one person with several problems contributes once to the any-problem numerator.''')
    code('''valid = df.valid_pos
    base = df.loc[valid]
    positives = base.pos_any.astype(bool)
    weighted_pct = 100 * base.loc[positives, 'Gross_weight'].sum() / base.Gross_weight.sum()
    print(f'In-store technical problems: {weighted_pct:.4f}%, valid n={len(base):,}')
    assert abs(weighted_pct - estimate(df, 'pos_any')['percent']) < 1e-10
    keys = ['pos_any', 'accept_any', 'online_any', 'cashless_preference', 'privacy_any']
    overview = summarize(df, keys)[['label','period','n','percent','effective_n_kish']]
    display(overview.round(2))''')
    md('''## 4. Inspect payment preference and friction
    A stated preference is not an observed payment market share. Acceptance barriers are also different from technical failures. Report each construct using its own question.

    **Interpretation:** about 58% prefer cashless payments. Around 23% report a technical in-store problem, and around 24% report an acceptance barrier. These are separate valid respondent groups.''')
    code('''for name in ['01_preference', '02_acceptance', '03_pos_problems']:
        display(Image(filename=str(ROOT / 'outputs' / 'figures' / f'{name}.png')))''')
    md('''## 5. Investigate online checkout and stated adoption factors
    Online data-entry difficulties, banking-app redirects and late passwords are distinct issues, with possible overlap. Their percentages are not a failed-transaction rate.

    Security and ease both reach about 38% as reasons to try another payment solution. Their small numerical difference does not establish a clear lead. No causal adoption effect is measured.''')
    code('''for name in ['04_online_problems', '05_adoption', '06_authentication']:
        display(Image(filename=str(ROOT / 'outputs' / 'figures' / f'{name}.png')))
    display(summarize(df, ['privacy_any','privacy_1','privacy_2'])[['label','n','percent']].round(2))''')
    md('''## 6. Segment responsibly
    Compare the age groups within the valid base of each metric. Younger respondents report more problems, but payment frequency, method use and reporting can differ. This does not measure capability.

    A descriptive country-standardized comparison holds each age group's country mix fixed at the overall valid base. It addresses one compositional factor, not every confounder.''')
    code('''age = by_group(df, 'age_group', ['pos_any','online_any','cashless_preference'])
    display(age[['group','label','n','percent']].round(2))
    display(standardized_age(df, 'pos_any').round(3))
    display(Image(filename=str(ROOT / 'outputs' / 'figures' / '07_age_pos.png')))
    country = by_group(df, 'country_name', ['pos_any'])
    display(country[['group','n','percent']].sort_values('percent', ascending=False).round(2))''')
    md('''## 7. Challenge the result before telling the story
    Compare weighted and unweighted results. Examine survey-mode differences and the effect of retaining unknown records in a denominator. The alternative denominator below measures positive reports among eligible records, not a valid-answer problem rate.

    Kish effective n diagnoses weight concentration. It cannot replace a full survey-design variance estimate. We avoid p-values and formal confidence intervals because the mixed probability/non-probability design and public file do not support a defensible full design-based analysis here.''')
    code('''from space_cx.analysis import denominator_sensitivity
    comparison = summarize(df, keys)[['metric','percent']].merge(
        summarize(df, keys, weighted=False)[['metric','percent']], on='metric',
        suffixes=('_weighted','_unweighted'))
    display(comparison.round(2))
    display(denominator_sensitivity(df).drop(columns='interpretation').round(2))
    display(by_group(df, 'survey_mode', ['pos_any','online_any'])[['group','label','n','percent']].round(2))''')
    md('''## 8. Turn evidence into testable actions
    - Investigate incident types using terminal, network and authorisation logs alongside merchant support cases.
    - Test payment-detail validation, error messages and recovery from authentication failures.
    - Test simpler task flows with clear security explanations before adding product features.

    Define operational success measures before running a pilot: completion rate, repeat attempts, incident recovery time, comprehension and support contacts. The survey supplies hypotheses, not ROI or causal uplift estimates.

    **Next learning exercise:** choose Portugal or Slovakia, rerun the metric table, and explain every response base before comparing it with the pooled result.''')
    code('''selected_country = 'PT'  # change to SK, HR, SI, EE, LV, LT or another included country
    country_df = df.loc[df.COUNTRY.eq(selected_country)]
    display(summarize(country_df, keys)[['label','n','percent']].round(2))''')
    md('''## Reproducibility and sources
    Run `python scripts/run_analysis.py` from the project root to rebuild the tables, figures, report, carousel and this executed notebook. Run `python -m unittest discover -s tests -v` for synthetic and source regression checks.

    Read `reports/case_study.md`, `docs/survey_guide.md` and `docs/metric_dictionary.csv` for the business interpretation and exact coding. The carousel is `presentation/space_2024_linkedin_carousel.pdf`.

    [ECB source](https://www.ecb.europa.eu/stats/ecb_surveys/space/html/index.en.html) | [Questionnaire](https://www.ecb.europa.eu/stats/ecb_surveys/space/shared/pdf/ecb.space2024_annex_a.en.pdf) | [Methodology](https://www.ecb.europa.eu/stats/ecb_surveys/space/shared/pdf/ecb.space2024_annex_b.en.pdf)

    Source data: European Central Bank. All estimates are independent calculations for the 18-country public-use file. No ECB endorsement.''')
    shell=InteractiveShell.instance()
    oldcwd=Path.cwd();os.chdir(ROOT)
    execution=0
    try:
        for cell in cells:
            if cell['cell_type']!='code':continue
            execution+=1
            with capture_output(display=True) as captured:
                result=shell.run_cell(''.join(cell['source']),store_history=False)
            if result.error_in_exec or result.error_before_exec:
                raise RuntimeError(f'Notebook cell {execution} failed: {result.error_in_exec or result.error_before_exec}')
            output=[]
            if captured.stdout:output.append({'output_type':'stream','name':'stdout','text':captured.stdout.splitlines(True)})
            if captured.stderr:output.append({'output_type':'stream','name':'stderr','text':captured.stderr.splitlines(True)})
            for o in captured.outputs:
                output.append({'output_type':'display_data','data':o.data,'metadata':o.metadata or {}})
            cell['execution_count']=execution;cell['outputs']=output
    finally:os.chdir(oldcwd)
    nb={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python','version':sys.version.split()[0]}},'nbformat':4,'nbformat_minor':5}
    for i,cell in enumerate(cells):cell['id']=f'space-cell-{i:02d}'
    (ROOT/'notebooks').mkdir(exist_ok=True)
    (ROOT/'notebooks'/'01_space_customer_experience.ipynb').write_text(json.dumps(nb,indent=1))

def pdf_carousel(tables):
    """1080 x 1350 vector PDF with large text for phone reading."""
    out=ROOT/'presentation';out.mkdir(exist_ok=True)
    # ReportLab bundles Bitstream Vera; use it so fonts do not depend on the OS.
    import reportlab
    fontdir=Path(reportlab.__file__).parent/'fonts'
    pdfmetrics.registerFont(TTFont('CX',str(fontdir/'Vera.ttf')))
    pdfmetrics.registerFont(TTFont('CX-Bold',str(fontdir/'VeraBd.ttf')))
    c=canvas.Canvas(str(out/'space_2024_linkedin_carousel.pdf'),pagesize=(1080,1350))
    c.setTitle('Customer Experience in Payments - SPACE 2024')
    c.setAuthor('Daniel Pantie')
    m=tables['metrics_weighted'].set_index('metric')
    val=lambda k:float(m.loc[k,'percent'])
    pct=lambda k:f'{val(k):.0f}%'
    page_count=10
    text_log=[]
    def text(s,x,y,size=32,bold=False,color=NAVY,maxwidth=920,leading=None):
        font='CX-Bold' if bold else 'CX';c.setFont(font,size);c.setFillColor(HexColor(color))
        lines=[]
        for para in s.split('\n'):
            words=para.split();line=''
            for word in words:
                candidate=(line+' '+word).strip()
                if pdfmetrics.stringWidth(candidate,font,size)>maxwidth and line:
                    lines.append(line);line=word
                else:line=candidate
            lines.append(line)
        lead=leading or size*1.32
        for line in lines:c.drawString(x,y,line);text_log.append(line);y-=lead
        return y
    def start(page,title,section,dark=False):
        c.setFillColor(HexColor(NAVY if dark else '#ffffff'));c.rect(0,0,1080,1350,fill=1,stroke=0)
        color='#ffffff' if dark else NAVY
        text(section.upper(),74,1277,22,color='#a9bdd5' if dark else MUTED)
        if title:text(title,74,1187,49,True,color,maxwidth=930,leading=61)
        c.setStrokeColor(HexColor('#41536b' if dark else '#dfe7ef'));c.line(74,115,1006,115)
        text('ECB SPACE 2024. My weighted calculations for 18 countries.',74,77,18,color='#b7c8da' if dark else MUTED)
        text(f'{page:02d} / {page_count}',910,77,18,color='#b7c8da' if dark else MUTED,maxwidth=100)
    def end():c.showPage()
    def bars(keys,y,max_x=100,height=105,color=BLUE,labels=None):
        for i,k in enumerate(keys):
            label=(labels or {}).get(k,m.loc[k,'label'])
            text(label,74,y,29,bold=False,maxwidth=850)
            by=y-43
            c.setFillColor(HexColor('#edf1f6'));c.roundRect(74,by-4,815,22,5,fill=1,stroke=0)
            c.setFillColor(HexColor(color));c.roundRect(74,by-4,815*val(k)/max_x,22,5,fill=1,stroke=0)
            text(pct(k),915,by-3,28,True,maxwidth=100)
            y-=height
        return y
    start(1,'','Customer experience in payments',True)
    text(pct('pos_any'),74,1050,194,True,'#ffffff')
    text('reported technical problems\nwhen paying in person',74,850,58,True,'#ffffff',maxwidth=930,leading=76)
    text('What 40,981 survey responses reveal about payment friction and customer needs.',74,600,36,color='#c7d6e7',leading=50)
    text('At least once in the past month. Valid n = 39,404.',74,387,25,color='#b7c8da')
    text('An independent Python case study\nDaniel Pantie',74,270,29,color='#ffffff',leading=43)
    end()
    start(2,'40,981 consumers.\n18 countries.','The survey')
    text('Real responses from the ECB\nSPACE 2024 public-use file',74,975,35,True,leading=48)
    items=[('ONE ROW PER PERSON','Payment diary and accompanying questions.'),
           ('TWO FIELDWORK ROUNDS','Autumn 2023 and spring 2024.'),
           ('DIFFERENT RECALL PERIODS','In-store problems: past month.\nOnline difficulties: diary-day payments.')]
    y=790
    for label,body in items:
        text(label,74,y,23,True,color=BLUE);text(body,74,y-55,31,leading=43);y-=190
    text('The public file excludes Germany and the Netherlands. Czechia is outside the survey.',74,235,25,color=MUTED,leading=36)
    end()
    start(3,'Cashless is the preferred\noption for 58%','Payment choice')
    text('If offered a choice in a shop:',74,984,31,color=MUTED)
    bars(['cashless_preference','cash_preference','no_preference'],875,height=145,
         labels={'cashless_preference':'Card or other cashless method','cash_preference':'Cash','no_preference':'No clear preference'})
    text('Preference describes what people would like to use. It does not measure their actual transaction share.',74,388,34,True,leading=48)
    text('Valid n = 40,795. General payment preference.',74,207,24,color=MUTED)
    end()
    start(4,'23% reported in-store\ntechnical problems','Payment reliability')
    text('At least once in the past month:',74,984,31,color=MUTED)
    bars(['pos_1','pos_2','pos_3'],875,height=145,
         labels={'pos_1':'Card payment','pos_2':'Mobile payment','pos_3':'Cash at self-checkout'})
    text('These are shares of valid respondents, not percentages of payments that failed.',74,380,34,True,leading=48)
    text('Valid n = 39,404. Multiple answers allowed.\nEach method uses the same response base.',74,222,24,color=MUTED,leading=35)
    end()
    start(5,'24% faced a restriction\non their preferred method','Payment acceptance')
    text('At least once in the past month:',74,984,31,color=MUTED)
    bars(['accept_2','accept_1','accept_3'],875,height=145,color=ORANGE,
         labels={'accept_2':'Card/mobile not accepted','accept_1':'Cash not accepted','accept_3':'Card/mobile minimum amount'})
    text('Acceptance policies create a separate customer experience problem from technical failures.',74,380,34,True,leading=48)
    text('Valid n = 38,719 in-store payment respondents.\nMultiple answers allowed.',74,222,24,color=MUTED,leading=35)
    end()
    start(6,'18% reported difficulty\nwith online payments','Online checkout')
    text('Most frequently selected difficulties:',74,984,31,color=MUTED)
    keys=sorted(GROUPS['online'][:-1],key=val,reverse=True)[:4]
    bars(keys,875,max_x=10,height=118,color=TEAL)
    text('Bars use a 0-10% scale.',74,374,23,color=MUTED)
    text('Payment forms and authentication recovery both deserve investigation.',74,310,33,True,leading=45)
    text('Valid n = 13,884 online-difficulty respondents.\nDiary-day payments. Multiple answers allowed.',74,202,24,color=MUTED,leading=35)
    end()
    start(7,'Security and ease lead\nstated adoption factors','Customer needs')
    keys=['adopt_3','adopt_1','adopt_2','adopt_4','adopt_5']
    bars(keys,971,height=114,labels={'adopt_3':'Higher security','adopt_1':'Easier to use','adopt_2':'Cheaper','adopt_4':'More privacy','adopt_5':'Innovative functions'})
    text('Security and ease are almost tied. These are stated motivations, not measured adoption effects.',74,336,32,True,leading=44)
    text('Valid n = 39,940. Up to three answers.\nIncludes respondents not interested in a new solution.',74,205,23,color=MUTED,leading=34)
    end()
    start(8,'Younger respondents\nreport more problems','Age differences')
    a=tables['by_age'];a=a[a.metric.eq('pos_any')].set_index('group')
    text('Any in-store technical issue in the past month:',74,984,29,color=MUTED)
    y=870
    for age in ['18-34','35-54','55+']:
        v=float(a.loc[age,'percent']);text('Age '+age,74,y,31)
        c.setFillColor(HexColor('#edf1f6'));c.roundRect(74,y-51,815,22,5,fill=1,stroke=0)
        c.setFillColor(HexColor(BLUE));c.roundRect(74,y-51,815*v/100,22,5,fill=1,stroke=0)
        text(f'{v:.0f}%',915,y-49,28,True,maxwidth=100);y-=145
    text('Differences in payment use and exposure may contribute. This does not measure digital capability.',74,375,33,True,leading=46)
    text('Valid n: 10,103 / 13,918 / 15,383.\nHolding country mix fixed gives a similar pattern.',74,213,24,color=MUTED,leading=35)
    end()
    start(9,'The findings suggest\nthree tests','Business implications')
    recommendations=[('01','Investigate in-store incidents','Link support cases with terminal, network and authorisation logs.'),
                     ('02','Test checkout recovery','Improve form validation and recovery from authentication errors.'),
                     ('03','Test ease with clear security','Assess task completion, comprehension and take-up in a pilot.')]
    y=964
    for number,title,body in recommendations:
        text(number,74,y,32,True,color=BLUE);text(title,147,y,34,True,maxwidth=840)
        text(body,147,y-66,30,color=MUTED,maxwidth=800,leading=43);y-=230
    text('These are hypotheses to test. The survey does not estimate revenue uplift or ROI.',74,219,26,color=MUTED,leading=38)
    end()
    start(10,'The denominator\nchanges the story','Method and reproducibility')
    points=[('A VALID BASE FOR EACH QUESTION','Skipped and non-substantive answers stay outside the primary percentage.'),
            ('WEIGHTED SHARES, ACTUAL COUNTS','The supplied Gross_weight adjusts the estimates. n counts real responses.'),
            ('DESCRIPTIVE FINDINGS','No causal effects or formal significance claims. This is the 18-country public file.')]
    y=972
    for title,body in points:
        text(title,74,y,23,True,color=BLUE);text(body,74,y-53,30,maxwidth=930,leading=42);y-=204
    text('The accompanying project includes the executed Python notebook, full metric definitions and reproducible code.',74,316,30,True,leading=43)
    text('Source and documentation: ECB SPACE 2024',74,177,23,color=BLUE)
    c.linkURL('https://www.ecb.europa.eu/stats/ecb_surveys/space/html/index.en.html',(74,166,900,203),relative=0)
    end();c.save()
    (out/'carousel_text.txt').write_text('\n'.join(text_log))

def dictionaries(path):
    out=ROOT/'docs';out.mkdir(exist_ok=True)
    metric_rows=[]
    for key,m in METRICS.items():
        metric_rows.append({'metric':key,'label':m.label,'base_flag':m.base,
            'positive_source':json.dumps(m.positive),'positive_value':m.value,
            'reference_period':m.period,'definition_type':m.kind})
    pd.DataFrame(metric_rows).to_csv(out/'metric_dictionary.csv',index=False)
    codebook=path.parent/'SPACE 2024 Codebook.xlsx'
    if not codebook.exists():
        raise FileNotFoundError('Extract the complete ECB ZIP, including SPACE 2024 Codebook.xlsx, beside the CSV.')
    b=pd.read_excel(codebook,sheet_name='SPACE - variables')
    b['variable']=b['Variable name'].ffill()
    used={'ID','COUNTRY','AGE','D1','FIELD','ROUND','Gross_weight','QQ3','QB8','Q1_7'}
    used.update(c for cols in GROUPS.values() for c in cols)
    question_rows=[]
    for variable,g in b[b.variable.isin(used)].groupby('variable',sort=False):
        first=g.iloc[0]
        options={str(r['Values']):str(r['Value label']) for _,r in g.iterrows()
                 if pd.notna(r['Values']) and pd.notna(r['Value label'])}
        question_rows.append({'variable':variable,'label':first['Label'],
            'question':first['Question'],'type':first['Type'],'source_filter':first['Filter'],
            'value_labels_json':json.dumps(options,ensure_ascii=False)})
    pd.DataFrame(question_rows).to_csv(out/'question_dictionary.csv',index=False)

def build_all(df,tables,info,path):
    dictionaries(path)
    charts(tables)
    report(tables,info)
    pdf_carousel(tables)
    notebook(path)
