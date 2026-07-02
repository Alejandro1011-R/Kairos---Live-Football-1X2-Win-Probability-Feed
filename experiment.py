"""Quick model bake-off to choose the best honest model (by test log-loss)."""
import numpy as np, pandas as pd, os
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import log_loss, accuracy_score

HERE=os.path.dirname(os.path.abspath(__file__)); DATA=os.path.join(HERE,"data")
df=pd.read_csv(os.path.join(DATA,"snapshots.csv"))
rng=np.random.RandomState(42); ids=df.match_id.unique(); rng.shuffle(ids)
test_ids=set(ids[:int(len(ids)*0.2)])
tr=df[~df.match_id.isin(test_ids)].copy(); te=df[df.match_id.isin(test_ids)].copy()
ytr,yte=tr.result.values,te.result.values
LEX=["A","D","H"]; HDA2LEX=[2,1,0]
def ll(model,Xte):
    p=model.predict_proba(Xte); idx=[list(model.classes_).index(c) for c in ["H","D","A"]]
    p=p[:,idx]; return log_loss(yte,p[:,HDA2LEX],labels=LEX), accuracy_score(yte,np.array(["H","D","A"])[p.argmax(1)])

FULL=["minute","time_remaining","goal_diff","home_goals","away_goals","red_home","red_away","shots_home","shots_away","xg_home","xg_away","xg_diff"]

# add engineered interaction + diffs
for d in (tr,te):
    d["mxgd"]=d.minute*d.goal_diff
    d["red_diff"]=d.red_home-d.red_away
    d["tr_gd"]=d.time_remaining*d.goal_diff

configs=[]
def add(name,model,cols): configs.append((name,model,cols))

add("logreg [min,gd]", make_pipeline(StandardScaler(),LogisticRegression(max_iter=3000)), ["minute","goal_diff"])
add("logreg [min,gd,min*gd]", make_pipeline(StandardScaler(),LogisticRegression(max_iter=3000)), ["minute","goal_diff","mxgd"])
add("logreg rich+inter", make_pipeline(StandardScaler(),LogisticRegression(max_iter=3000)), ["minute","time_remaining","goal_diff","mxgd","tr_gd","xg_diff","red_diff","shots_home","shots_away"])
add("GBM reg (full)", HistGradientBoostingClassifier(learning_rate=0.05,max_leaf_nodes=31,min_samples_leaf=300,l2_regularization=1.0,max_iter=1500,early_stopping=True,validation_fraction=0.15,n_iter_no_change=25,random_state=42), FULL)
add("GBM light reg", HistGradientBoostingClassifier(learning_rate=0.07,max_leaf_nodes=63,min_samples_leaf=80,l2_regularization=0.5,max_iter=2000,early_stopping=True,validation_fraction=0.15,n_iter_no_change=30,random_state=42), FULL)
add("GBM +sigmoid cal", CalibratedClassifierCV(HistGradientBoostingClassifier(learning_rate=0.07,max_leaf_nodes=63,min_samples_leaf=80,max_iter=2000,early_stopping=True,validation_fraction=0.15,n_iter_no_change=30,random_state=42),method="sigmoid",cv=3), FULL)

print(f"{'model':28} {'log_loss':>9} {'acc':>7}")
rows=[]
for name,model,cols in configs:
    model.fit(tr[cols],ytr)
    L,A=ll(model,te[cols]); rows.append((name,L,A))
    print(f"{name:28} {L:>9.4f} {A:>7.4f}")
best=min(rows,key=lambda r:r[1])
print(f"\nBEST: {best[0]}  log_loss={best[1]:.4f}")
