import pandas as pd, numpy as np, re
from pathlib import Path
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 60)
RUN = Path("/mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag")
d = pd.read_csv(RUN/"data/linked.csv", parse_dates=["t0","t1","t2","t3b","t3h","t3","t3_au","consent_ended","t_app","t_dec","t_tga"])
c = pd.read_csv(RUN/"data/cohort.csv")
sus = ["dimethyl","trastuzumab emtansine","ado-trastuzumab emtansine","fam-trastuzumab deruxtecan","trastuzumab deruxtecan","lutetium","lutetium vipivotide tetraxetan","lutetium lu-177 vipivotide tetraxetan","lutetium oxodotreotide","fampridine","dalfampridine","voxilaprevi","voxilaprevir","retigabine","ezogabine","c1 inhibitor","chlormethine","chenodeoxycholic acid","glibenclamide","ciclosporin","glycopyrronium","beclometasone","mometasone","leuprorelin","norethisterone","oestrogens conjugated","methylthioninium","treosulfan","botulinum toxin type a","pancreas powder","para-aminosalicylic acid","human coagulation factor viii","human von willebrand factor","alpha1-proteinase inhibitor","polidocanol","boceprevir","nonacog gamma","acetylsalicylic acid","melphalan flufenamide","crisantaspase","asparaginase erwinia chrysanthemi","tegafur","artenimol","casirivimab","imdevimab","remdesivir","sotrovimab","nirmatrelvir","molnupiravir","tixagevimab","samidorphan l","birch bark extract","birch triterpenes","ferric coordination complex","angiotensin ii","xenon xe-129 hyperpolarized","eptacog beta","vonicog alfa","efmoroctocog alfa","eftrenonacog alfa","tisagenlecleucel","axicabtagene ciloleucel","onasemnogene abeparvovec","andexanet alfa","sipuleucel-t","dinutuximab","dinutuximab beta"]
cols=["substance","t0","t0_source","t1","t2","t3b","t3h","t3","t_tga","excluded_old","match_names"]
x = d[d.substance.isin(sus)][cols].sort_values("substance")
print(x.to_string())
print("\nnot in cohort:", [s for s in sus if s not in set(d.substance)])
print("\n--- cohort rows for a few ---")
print(c[c.substance.isin(["dimethyl","trastuzumab emtansine","ado-trastuzumab emtansine","lutetium lu-177 vipivotide tetraxetan","lutetium vipivotide tetraxetan","fampridine","dalfampridine","voxilaprevi","voxilaprevir","melphalan flufenamide","c1 inhibitor"])][["substance","fda_first","fda_name","ema_first","ema_name","t0","t0_source","aliases"]].to_string())
