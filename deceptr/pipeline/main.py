"""
DECEPTR v1 — Entry point du pipeline
Lance la boucle principale de traitement toutes les POLL_INTERVAL secondes.
"""
import asyncio
import logging
import sys

from config import POLL_INTERVAL, LOG_LEVEL
from collector   import Collector
from normalizer  import Normalizer
from enricher    import Enricher
from correlator  import Correlator
from risk_scorer import RiskScorer
from detector    import Detector
from alerter     import Alerter
from storage     import Storage
from responder   import Responder
from misp_client import MISPClient

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("deceptr.main")


class Pipeline:
    """
    Orchestre les 7 étapes du pipeline DECEPTR.
    Chaque étape est indépendante et peut être testée séparément.

    Flux :
      ES(cowrie-*) → Collector → Normalizer → Enricher → Correlator
                   → RiskScorer → Detector → Alerter → Storage(ES+MySQL)
    """

    def __init__(self):
        self.collector   = Collector()
        self.normalizer  = Normalizer()
        self.enricher    = Enricher()
        self.correlator  = Correlator()
        self.risk_scorer = RiskScorer()
        self.detector    = Detector()
        self.alerter     = Alerter()
        self.storage     = Storage()
        self.responder   = Responder()
        self.misp        = MISPClient()

    async def start(self):
        log.info("DECEPTR Pipeline v1 démarrage...")
        await self.storage.connect()
        await self.enricher.load_feodo()
        log.info(f"Pipeline actif — polling toutes les {POLL_INTERVAL}s")

        while True:
            try:
                await self._run_cycle()
            except Exception as e:
                log.error(f"Erreur cycle pipeline : {e}", exc_info=True)
            await asyncio.sleep(POLL_INTERVAL)

    async def _run_cycle(self):
        # Étape 1 — Collecte
        raw_events = await self.collector.collect()
        if not raw_events:
            return

        log.info(f"[1/7] Collecté {len(raw_events)} nouveaux événements Cowrie")

        for raw in raw_events:
            try:
                # Étape 2 — Normalisation
                event = self.normalizer.normalize(raw)
                if not event:
                    continue

                # Étape 3 — Enrichissement
                event = await self.enricher.enrich(event)

                # Étape 4 — Corrélation + MITRE ATT&CK
                event = self.correlator.correlate(event)

                # Étape 5 — Risk Scoring
                event = self.risk_scorer.score(event)

                # Étape 6 — Détection
                alerts = self.detector.detect(event)

                # Étape 7 — Alertes + Stockage
                await self.alerter.process(event, alerts)
                await self.storage.save(event, alerts)

                # Étape 8 — Active Response
                await self.responder.process(event, alerts)

                # Étape 9 — Threat Intel Export (MISP)
                if event.get("severity") in ["HIGH", "CRITICAL"]:
                    await self.misp.export_ioc(event)

            except Exception as e:
                log.error(f"Erreur traitement événement : {e}", exc_info=True)


async def main():
    pipeline = Pipeline()
    try:
        await pipeline.start()
    except KeyboardInterrupt:
        log.info("Pipeline arrêté.")

if __name__ == "__main__":
    asyncio.run(main())
