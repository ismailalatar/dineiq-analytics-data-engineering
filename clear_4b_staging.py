"""Mark 4B outputs as PENDING_VALIDATION - clear all staging tables.
SRS Ref: Step 13/14 + Anti-Shortcut 10 - 4B used baseline, not Student 3's Python pipeline.
"""
from app import create_app
from app.extensions import db
from app.models.integration import (Recommendation, DualPipelineComparison,
                                    SlowMovingDish, LocationIntelligence,
                                    ChannelIntelligence, WhatIfResult,
                                    SurpriseModificationReadiness)

def clear_all():
    app = create_app()
    with app.app_context():
        cleared = {}
        for m in [Recommendation, DualPipelineComparison, SlowMovingDish,
                  LocationIntelligence, ChannelIntelligence, WhatIfResult,
                  SurpriseModificationReadiness]:
            n = m.query.count()
            m.query.delete()
            cleared[m.__tablename__] = n
        db.session.commit()
        print("PENDING_VALIDATION - cleared 4B staging tables:")
        for k, v in cleared.items():
            print(f"  {k}: {v} rows removed")
        print("\nAll 4B outputs marked PENDING_VALIDATION.")
        print("Will NOT import again until SRS compliance confirmed.")

if __name__ == "__main__":
    clear_all()