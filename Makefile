# Comandi di test e controllo. I test sono script: si eseguono con il venv della loro cartella.
PY  := pipeline/.venv/bin/python
SPY := service/.venv/bin/python

.PHONY: test-fast test lint validate ci

test-fast:
	$(PY) network/test_rete_firenze.py
	$(PY) geometry/test_geometrie_firenze.py
	$(PY) scene/firenze_novoli/test_build.py
	$(SPY) service/test_service.py

test: test-fast validate
	$(PY) analysis/test_accessibilita.py
	$(PY) scenarios/test_scenari.py
	$(PY) shadow/test_ombre.py
	$(SPY) nl/firenze_novoli/test_nl.py

lint:
	ruff check .

validate:
	$(PY) contracts/validate.py

# Quello che gira la CI: solo i controlli che non richiedono data/.
ci: lint validate
	$(PY) geometry/test_geometrie_firenze.py
	$(PY) scene/firenze_novoli/test_build.py
