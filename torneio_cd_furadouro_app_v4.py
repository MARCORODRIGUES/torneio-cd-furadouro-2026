import streamlit as st
import json, os
from itertools import combinations

st.set_page_config(page_title="Torneio de Natal CD Furadouro 2026", layout="wide")
st.title("🎄 Torneio de Natal CD Furadouro 2026")
st.caption("Acompanhamento público e gestão reservada do torneio")

GROUPS = {
"A":["AD Ovarense","CD Estarreja","Gverreiros Vale Domingos B","FANTASMA"],
"B":["FC Cesarense","CD Feirense","Gverreiros Vale Domingos C","CB Albergaria-a-velha"],
"C":["AD Valonguense","AD Ovarense B","UD Mourisquense","CCR Valega B"],
"D":["Gverreiros Vale Domingos A","CD Loureiro","CCR Valega","EF Rui Dolores"],
}
# Mode selector and organization password gate
mode = st.sidebar.radio("Modo", ["👀 Consulta pública", "🔐 Organização"])
admin = False
if mode == "🔐 Organização":
    try:
        expected_password = st.secrets["admin_password"]
    except Exception:
        expected_password = "furadouro2026"
        st.sidebar.warning("Password provisória ativa. Configure admin_password nos Secrets do Streamlit.")
    entered = st.sidebar.text_input("Password da organização", type="password")
    admin = entered == expected_password
    if not admin:
        st.sidebar.info("Introduza a password para ativar a edição.")
    else:
        st.sidebar.success("Modo de edição ativo.")

FILE="resultados_torneio.json"
if os.path.exists(FILE):
    try:
        with open(FILE,"r",encoding="utf-8") as f: scores=json.load(f)
    except: scores={}
else: scores={}
if "scores" not in st.session_state: st.session_state.scores=scores

def getscore(mid):
    return st.session_state.scores.get(mid, [None,None])
def save(mid,a,b):
    st.session_state.scores[mid]=[a,b]
    with open(FILE,"w",encoding="utf-8") as f: json.dump(st.session_state.scores,f,ensure_ascii=False,indent=2)

def match(mid, label, t1, t2):
    st.markdown(f"**{label}**")
    if not t1 or not t2:
        st.info("Equipas ainda por determinar.")
        return None
    old=getscore(mid)
    if not admin:
        if old[0] is None or old[1] is None:
            st.caption("Resultado ainda não registado.")
        else:
            st.markdown(f"**{t1}  {old[0]} – {old[1]}  {t2}**")
        return None
    c1,c2,c3=st.columns([4,1,4])
    with c1: st.write(t1)
    with c2:
        a=st.number_input(" ",min_value=0,step=1,value=old[0],key=mid+"a",label_visibility="collapsed")
    with c3:
        b=st.number_input(" ",min_value=0,step=1,value=old[1],key=mid+"b",label_visibility="collapsed")
        st.write(t2)
    if a is not None and b is not None: save(mid,a,b)
    else:
        st.session_state.scores.pop(mid,None)
        with open(FILE,"w",encoding="utf-8") as f: json.dump(st.session_state.scores,f,ensure_ascii=False,indent=2)
    if a is None or b is None or a==b: return None
    return t1 if a>b else t2

def complete(mid):
    x=getscore(mid)
    return x[0] is not None and x[1] is not None
def winner(mid,t1,t2):
    if not t1 or not t2 or not complete(mid): return None
    a,b=getscore(mid)
    return t1 if a>b else t2 if b>a else None
def loser(mid,t1,t2):
    w=winner(mid,t1,t2)
    if not w: return None
    return t2 if w==t1 else t1

# Group matches and standings
group_matches={}
standings={}
for g,teams in GROUPS.items():
    group_matches[g]=[(f"G{g}{i}",teams[a],teams[b]) for i,(a,b) in enumerate(combinations(range(4),2),1)]
    rows={t:{"P":0,"V":0,"E":0,"D":0,"GM":0,"GS":0,"DG":0} for t in teams}
    for mid,t1,t2 in group_matches[g]:
        if complete(mid):
            a,b=getscore(mid)
            rows[t1]["GM"]+=a; rows[t1]["GS"]+=b; rows[t1]["DG"]+=a-b
            rows[t2]["GM"]+=b; rows[t2]["GS"]+=a; rows[t2]["DG"]+=b-a
            if a>b: rows[t1]["P"]+=3;rows[t1]["V"]+=1;rows[t2]["D"]+=1
            elif b>a: rows[t2]["P"]+=3;rows[t2]["V"]+=1;rows[t1]["D"]+=1
            else: rows[t1]["P"]+=1;rows[t2]["P"]+=1;rows[t1]["E"]+=1;rows[t2]["E"]+=1
    # Sorting: points; for exactly-two tie, head-to-head; otherwise DG then goals scored.
    def sort_key(t): return (rows[t]["P"],rows[t]["DG"],rows[t]["GM"])
    sortedteams=sorted(teams,key=sort_key,reverse=True)
    # Apply head-to-head for exactly two tied teams (simple adjacent tie group)
    i=0
    while i<len(sortedteams):
        j=i+1
        while j<len(sortedteams) and rows[sortedteams[j]]["P"]==rows[sortedteams[i]]["P"]: j+=1
        tied=sortedteams[i:j]
        if len(tied)==2:
            h=None
            for mid,x,y in group_matches[g]:
                if {x,y}==set(tied) and complete(mid):
                    a,b=getscore(mid); h=(x if a>b else y if b>a else None)
            if h: sortedteams[i:j]=[h, tied[1] if tied[0]==h else tied[0]]
        i=j
    standings[g]=sortedteams

def all_groups_done():
    return all(complete(mid) for g in GROUPS for mid,_,_ in group_matches[g])


def groupstats(g,t):
    # compute stats again from recorded scores
    d={"P":0,"GM":0,"GS":0,"DG":0}
    for mid,x,y in group_matches[g]:
        if complete(mid):
            a,b=getscore(mid)
            if x==t:
                d["GM"]+=a;d["GS"]+=b;d["DG"]+=a-b
                d["P"]+=3 if a>b else 1 if a==b else 0
            elif y==t:
                d["GM"]+=b;d["GS"]+=a;d["DG"]+=b-a
                d["P"]+=3 if b>a else 1 if a==b else 0
    return d


tabs=st.tabs(["⚽ Resultados dos grupos","📊 Classificações","🏆 Fase final","ℹ️ Informação","💾 Backup"])
with tabs[0]:
    for g,ms in group_matches.items():
        with st.expander(f"Grupo {g}",expanded=True):
            for mid,t1,t2 in ms: match(mid,f"{t1} vs {t2}",t1,t2)
with tabs[1]:
    for g,teams in standings.items():
        st.subheader(f"Grupo {g}")
        st.dataframe([{"Lugar":i+1,"Equipa":t,**{k:standings_stats(g,t,k) for k in []}} for i,t in enumerate(teams)] if False else
                     [{"Lugar":i+1,"Equipa":t,"Pontos":groupstats(g,t)["P"],"GM":groupstats(g,t)["GM"],"GS":groupstats(g,t)["GS"],"DG":groupstats(g,t)["DG"]} for i,t in enumerate(teams)],hide_index=True,use_container_width=True)

# Final phase only unlocked once group phase complete
with tabs[2]:
    if not all_groups_done():
        st.info("A fase final será disponibilizada quando os 24 jogos dos grupos tiverem resultados.")
    else:
        ranks={g:standings[g] for g in GROUPS}
        st.header("Acesso ao Ouro — jogos de apuramento")
        AP=[("AP1",ranks["A"][1],ranks["B"][2]),("AP2",ranks["B"][1],ranks["A"][2]),("AP3",ranks["C"][1],ranks["D"][2]),("AP4",ranks["D"][1],ranks["C"][2])]
        apwins={}; aplosers={}
        for mid,x,y in AP:
            apwins[mid]=match(mid,f"{mid}: {x} vs {y}",x,y)
            aplosers[mid]=loser(mid,x,y)
        if all(complete(m) for m,_,_ in AP):
            st.header("Ouro — quartos de final")
            gold=[ranks["A"][0],ranks["B"][0],ranks["C"][0],ranks["D"][0],apwins["AP1"],apwins["AP2"],apwins["AP3"],apwins["AP4"]]
            qfpairs=[("OQF1",gold[0],gold[7]),("OQF2",gold[3],gold[4]),("OQF3",gold[1],gold[6]),("OQF4",gold[2],gold[5])]
            qw={}; ql={}
            for mid,x,y in qfpairs:
                qw[mid]=match(mid,mid,x,y);ql[mid]=loser(mid,x,y)
            if all(complete(m) for m,_,_ in qfpairs):
                st.header("Ouro — semifinais e classificação")
                pairs=[("OSF1",qw["OQF1"],qw["OQF2"]),("OSF2",qw["OQF3"],qw["OQF4"]),("O5SF1",ql["OQF1"],ql["OQF2"]),("O5SF2",ql["OQF3"],ql["OQF4"])]
                wins={}
                for mid,x,y in pairs: wins[mid]=match(mid,mid,x,y)
                if all(complete(m) for m,_,_ in pairs[:2]):
                    match("O3","Ouro 3.º/4.º",loser("OSF1",qw["OQF1"],qw["OQF2"]),loser("OSF2",qw["OQF3"],qw["OQF4"]))
                    match("OFinal","Final Ouro",wins["OSF1"],wins["OSF2"])
                if all(complete(m) for m,_,_ in pairs[2:]):
                    match("O7","Ouro 7.º/8.º",loser("O5SF1",ql["OQF1"],ql["OQF2"]),loser("O5SF2",ql["OQF3"],ql["OQF4"]))
                    match("O5","Ouro 5.º/6.º",wins["O5SF1"],wins["O5SF2"])
            # Silver 8-team bracket: 4th places and AP losers, with pairing choices fixed to avoid group rematches when possible
            if all(complete(m) for m,_,_ in AP):
                silver=[ranks["A"][3],ranks["B"][3],ranks["C"][3],ranks["D"][3],aplosers["AP1"],aplosers["AP2"],aplosers["AP3"],aplosers["AP4"]]
                st.header("Prata — quartos de final (cruzamento fixo)")
                sq=[("SQF1",silver[0],silver[7]),("SQF2",silver[1],silver[6]),("SQF3",silver[2],silver[5]),("SQF4",silver[3],silver[4])]
                sw={};sl={}
                for mid,x,y in sq: sw[mid]=match(mid,mid,x,y);sl[mid]=loser(mid,x,y)
                if all(complete(m) for m,_,_ in sq):
                    st.header("Prata — semifinais")
                    ss=[("SSF9_1",sw["SQF1"],sw["SQF2"]),("SSF9_2",sw["SQF3"],sw["SQF4"]),("SSF13_1",sl["SQF1"],sl["SQF2"]),("SSF13_2",sl["SQF3"],sl["SQF4"])]
                    ssw={}
                    for mid,x,y in ss: ssw[mid]=match(mid,mid,x,y)
                    if all(complete(m) for m,_,_ in ss[:2]):
                        match("S11", "Prata 11.º/12.º", loser("SSF9_1",sw["SQF1"],sw["SQF2"]),loser("SSF9_2",sw["SQF3"],sw["SQF4"]))
                        match("S9", "Prata 9.º/10.º", ssw["SSF9_1"],ssw["SSF9_2"])
                    if all(complete(m) for m,_,_ in ss[2:]):
                        match("S15","Prata 15.º/16.º",loser("SSF13_1",sl["SQF1"],sl["SQF2"]),loser("SSF13_2",sl["SQF3"],sl["SQF4"]))
                        match("S13","Prata 13.º/14.º",ssw["SSF13_1"],ssw["SSF13_2"])
with tabs[3]:
    st.header("ℹ️ Informação do torneio")
    st.subheader("Formato")
    st.write("16 equipas, 4 grupos de 4. Cada grupo disputa todos contra todos (6 jogos).")
    st.write("Os 1.º classificados seguem diretamente para Ouro. Os 2.º e 3.º classificados disputam jogos de apuramento. Os 4.º classificados e os derrotados desses jogos integram a Prata.")
    st.subheader("Critérios de desempate na fase de grupos")
    st.markdown("""
    1. Pontos (vitória: 3; empate: 1; derrota: 0).
    2. Se **exatamente duas equipas** estiverem empatadas em pontos: confronto direto.
    3. Se **três ou mais equipas** estiverem empatadas: diferença de golos (DG) e golos marcados (GM) nos jogos do grupo.
    4. Se persistir o empate: diferença de golos total no grupo, golos marcados totais, fair-play (menos cartões) e, por último, sorteio.
    """)
    st.warning("A ordenação automática atual é provisória em alguns cenários de empate. Confirmar manualmente os casos complexos.")
    st.subheader("Eliminatórias")
    st.write("Em caso de empate, decisão por penáltis: 3 penáltis por equipa e, se necessário, morte súbita. Sem prolongamento.")
    st.subheader("Contactos e apoio")
    st.write("Organização: CD Furadouro")
    st.write("Contacto: [preencher contacto de apoio]")
    st.write("Local: [preencher local do torneio]")
    st.write("Horário: [preencher]")
    st.caption("Esta informação pode ser atualizada pela organização.")
with tabs[4]:
    st.write("Cópia de segurança dos resultados.")
    if admin:
        st.download_button("⬇️ Descarregar backup JSON",json.dumps(st.session_state.scores,ensure_ascii=False,indent=2),"backup_torneio.json","application/json")
        if st.button("⚠️ Limpar TODOS os resultados"):
            st.session_state.scores={}
            with open(FILE,"w",encoding="utf-8") as f: json.dump({},f)
            st.rerun()
    else:
        st.info("Área reservada à organização.")
