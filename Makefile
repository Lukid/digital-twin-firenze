# Comandi di test e controllo. I test sono script: si eseguono con il venv della loro cartella.
PY  := pipeline/.venv/bin/python
SPY := service/.venv/bin/python

.PHONY: test-fast test lint validate ci impronte

test-fast:
	$(PY) network/test_rete_firenze.py
	$(PY) geometry/test_geometrie_firenze.py
	$(PY) scene/firenze_novoli/test_build.py
	$(SPY) service/test_service.py
	$(SPY) service/test_schede.py
	$(SPY) service/test_mcp_remoto.py

test: test-fast validate
	$(PY) analysis/test_accessibilita.py
	$(PY) scenarios/test_scenari.py
	$(PY) scenarios/test_costo_filare.py
	$(PY) shadow/test_ombre.py
	$(SPY) nl/firenze_novoli/test_nl.py

lint:
	$(PY) -m ruff check .

validate:
	$(PY) contracts/validate.py

# D39: sha256 dei file generati con geometrie, per il confronto fra Mac e worker
impronte:
	@bash scripts/impronte.sh

# Quello che gira la CI: solo i controlli che non richiedono data/ né i file
# degli edifici, che non sono nel repo pubblico.
ci: lint validate
	$(PY) service/test_schede.py
