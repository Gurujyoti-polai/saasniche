"""Pipeline runner module."""


def run() -> None:
    """Run the implemented SaasNiche pipeline stages in order."""

    from saas_niche.blueprints.blueprint_gen import run as run_blueprints
    from saas_niche.classifier.classifier import run as run_classifier
    from saas_niche.crawler.reddit_crawler import run as run_crawler
    from saas_niche.scorer.scorer import run as run_scorer

    print("[pipeline] crawl")
    run_crawler()

    print("[pipeline] classify")
    run_classifier()

    print("[pipeline] score")
    run_scorer()

    print("[pipeline] blueprint")
    run_blueprints()
