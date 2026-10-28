# AI Council – eksperimentinis įrodymų tikrinimo branduolys (R0)

**R0 nėra pilna kelių modelių AI Council sistema.** Tai pirmoji atskirai išleidžiama, be modelių ir be tinklo veikianti kodo audito įrodymų tikrinimo dalis.

Pagrindinis projekto tikslas – **sąžiningai išmatuoti**, ar kelių AI specialistų sistema patikimesnė už vieną stiprų modelį esant palyginamam bendram biudžetui. Toks pranašumas **dar neįrodytas**.

## Paleidimas

Reikia Python 3.12 ar naujesnės versijos; nieko papildomai diegti nereikia.

```powershell
python -B -m examples.offline_demo
python -B -m unittest discover -s tests -v
python -B scripts/check_public_tree.py
```

Demonstracija naudoja tik sintetinius failus. Tikrinamo kodo ji **nevykdo**. Privatūs vertinimo rinkiniai, modelių įrašai, vidinė Git istorija, prisijungimai ir darbo žurnalai neįtraukti.

Prisidėti galima per **GitHub Issues**, vėliau – **GitHub Discussions**. Asmeninis el. paštas neskelbiamas. Projektą prižiūrintis asmuo išlieka atsakingas už pakeitimų patvirtinimą.

Licencijos kandidatas: **Apache-2.0**. Prieš viešinimą būtinas atskiras savininko patvirtinimas, kodo kilmės ir licencijų patikra.
