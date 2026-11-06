"""One command regenerates audited tables, charts, report and executed notebook."""
from pathlib import Path
import sys
import argparse
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from space_cx.analysis import prepare,write_results
from download_data import download

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,help='Existing original ECB CSV; default downloads if absent.')
    args=parser.parse_args()
    path=args.data or download()
    raw=pd.read_csv(path)
    df=prepare(raw)
    tables,info=write_results(df,raw,path,ROOT/'outputs'/'tables')
    from build_outputs import build_all
    build_all(df,tables,info,path)
    print(f'Completed: {len(df):,} respondents; {df.COUNTRY.nunique()} countries.')
    print('Open notebooks/01_space_customer_experience.ipynb and reports/case_study.md.')

if __name__=='__main__':main()
