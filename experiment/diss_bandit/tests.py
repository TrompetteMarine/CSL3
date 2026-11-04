# Bot entry points for `otree test` (oTree 6 imports <app>.tests).
# Implementations live in the app module next to the live method they drive.
# Absolute import on purpose: it resolves to the already-loaded module and avoids
# re-executing the model definitions under a second module name.
from diss_bandit import PlayerBot, call_live_method  # noqa: F401
