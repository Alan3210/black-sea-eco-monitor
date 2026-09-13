from agents.news_agent.location_resolver import (
    normalize_location_name,
)
from agents.news_agent.coordinate_resolver import (
    resolve_coordinates,
)
from agents.news_agent.oil_spill_evidence_guard import (
    apply_oil_spill_evidence_guard,
)
from agents.news_agent.event_store import (
    EventStore,
)
from agents.news_agent.event_lifecycle import (
    detect_lifecycle_status,
)

from agents.news_agent.agent import NewsAgent
from agents.news_agent.category_evidence_guard import (
    apply_category_evidence_guard,
)
from agents.news_agent.event_builder import (
    build_environmental_event,
)
from agents.news_agent.event_gate import (
    evaluate_event_candidate,
    EventGateAction,
)
from agents.news_agent.filter import (
    filter_black_sea_incidents,
)
from agents.news_agent.freshness_gate import (
    evaluate_news_freshness,
)
from agents.news_agent.incident_evidence_guard import (
    apply_incident_evidence_guard,
)
from agents.news_agent.lifecycle_guard import (
    apply_lifecycle_guard,
)
from agents.news_agent.llm_resilience import (
    classify_news_with_retry,
)
from agents.news_agent.rule_classifier import (
    classify_news_item,
)
from agents.news_agent.event_correlation import (
    EventCandidate,
    cluster_event_candidates,
)


BATCH_LIMIT = None


def print_classification_result(
    label,
    result,
):

    print(label)

    print(
        f"  Classification: "
        f"{result.classification.value}"
    )

    print(
        f"  Category: "
        f"{result.category}"
    )

    print(
        f"  Location: "
        f"{result.location_name}"
    )

    print(
        f"  Black Sea region: "
        f"{result.is_black_sea_region}"
    )

    print(
        f"  Confidence: "
        f"{result.confidence}"
    )

    print(
        f"  New event: "
        f"{result.is_new_event}"
    )

    print(
        f"  Event date: "
        f"{result.event_date}"
    )

    print(
        f"  Reason: "
        f"{result.reason}"
    )



def apply_event_lifecycle(
    *,
    event_store,
    event_id,
    item,
    evidence_id,
):

    lifecycle_decision = (
        detect_lifecycle_status(
            item.title,
            getattr(
                item,
                "summary",
                "",
            ) or "",
        )
    )

    history_id = event_store.update_status(
        event_id=event_id,
        new_status=(
            lifecycle_decision.status
        ),
        reason=(
            lifecycle_decision.reason
        ),
        evidence_id=evidence_id,
    )

    print()
    print("EVENT LIFECYCLE")

    print(
        f"  Detected status: "
        f"{lifecycle_decision.status}"
    )

    print(
        f"  Reason: "
        f"{lifecycle_decision.reason}"
    )

    if history_id is None:

        print(
            "  Status unchanged."
        )

    else:

        print(
            "  Status updated."
        )

        print(
            f"  History ID: "
            f"{history_id}"
        )


def main():

    agent = NewsAgent()
    event_store = EventStore()

    print("Collecting news...")
    print()

    items = agent.collect()

    print(
        f"Collected: {len(items)}"
    )

    relevant_items = agent.analyze(
        items
    )

    print(
        f"Environmentally relevant: "
        f"{len(relevant_items)}"
    )

    candidates = filter_black_sea_incidents(
        relevant_items
    )

    print(
        f"Black Sea candidates: "
        f"{len(candidates)}"
    )

    print()

    fresh_candidates = []

    print("FRESHNESS CHECK")
    print()

    for index, item in enumerate(
        candidates,
        start=1,
    ):

        freshness = evaluate_news_freshness(
            item
        )

        print(
            f"{index}. {item.title}"
        )

        print(
            f"   Published: {item.published_at}"
        )

        print(
            f"   Fresh: {freshness.is_fresh}"
        )

        if freshness.age_days is not None:

            print(
                f"   Age: "
                f"{freshness.age_days:.1f} days"
            )

        print(
            f"   Reason: {freshness.reason}"
        )

        if freshness.is_fresh:

            fresh_candidates.append(
                item
            )

            print(
                "   PRELIMINARY ACTION: "
                "SEND_TO_LLM"
            )

        else:

            print(
                "   FINAL ACTION: "
                "IGNORE_STALE"
            )

        print()

    print("=" * 80)
    print()

    print(
        f"Fresh candidates: "
        f"{len(fresh_candidates)}"
    )

    if BATCH_LIMIT is None:

        selected_candidates = (
            fresh_candidates
        )

    else:

        selected_candidates = (
            fresh_candidates[:BATCH_LIMIT]
        )

    print(
        f"Processing with LLM: "
        f"{len(selected_candidates)}"
    )

    print()
    print("=" * 80)
    print()

    event_candidates = []

    for index, item in enumerate(
        selected_candidates,
        start=1,
    ):

        print(
            f"{index}. {item.title}"
        )

        print(
            f"Source: {item.source}"
        )

        print(
            f"Published: {item.published_at}"
        )

        print()

        rule_result = classify_news_item(
            item
        )

        print_classification_result(
            "RULE-BASED",
            rule_result,
        )

        print()

        try:

            llm_result = classify_news_with_retry(
                item
            )

            print_classification_result(
                "LLM",
                llm_result,
            )

            print()

            category_guard_result = (
                apply_category_evidence_guard(
                    item,
                    llm_result,
                )
            )

            print_classification_result(
                "CATEGORY EVIDENCE GUARD",
                category_guard_result,
            )

            print()

            oil_spill_guard_result = (
                apply_oil_spill_evidence_guard(
                    item,
                    category_guard_result,
                )
            )

            print_classification_result(
                "OIL SPILL EVIDENCE GUARD",
                oil_spill_guard_result,
            )

            print()

            lifecycle_guard_result = (
                apply_lifecycle_guard(
                    item,
                    oil_spill_guard_result,
                )
            )

            print_classification_result(
                "LIFECYCLE GUARD",
                lifecycle_guard_result,
            )

            print()

            final_guarded_result = (
                apply_incident_evidence_guard(
                    lifecycle_guard_result,
                    rule_result,
                )
            )

            print_classification_result(
                "INCIDENT EVIDENCE GUARD",
                final_guarded_result,
            )

            print()

            normalized_result = (
                final_guarded_result.model_copy(
                    update={
                        "location_name":
                        normalize_location_name(
                            final_guarded_result.location_name
                        )
                    }
                )
            )

            print_classification_result(
                "LOCATION RESOLVER",
                normalized_result,
            )

            print()

            gate_decision = (
                evaluate_event_candidate(
                    normalized_result
                )
            )

            print("EVENT GATE")

            print(
                f"  FINAL ACTION: "
                f"{gate_decision.action.value.upper()}"
            )

            print(
                f"  Reason: "
                f"{gate_decision.reason}"
            )

            if (
                gate_decision.action
                == EventGateAction.create_event
            ):

                event = build_environmental_event(
                    item,
                    normalized_result,
                )

                print()
                print("EVENT BUILDER")

                print(
                    event.model_dump_json(
                        indent=2
                    )
                )

                event_candidates.append(
                    EventCandidate(
                        item=item,
                        classification=normalized_result,
                    )
                )

                print()
                print("EVENT STORE")

                item_url = getattr(
                    item,
                    "url",
                    None,
                )

                existing_event_id = (
                    event_store.find_event_by_evidence_url(
                        item_url
                    )
                )

                found_by_evidence_url = (
                    existing_event_id is not None
                )

                if existing_event_id is None:

                    existing_event_id = (
                        event_store.find_matching_event(
                            category=(
                                normalized_result.category.value
                            ),
                            location_name=(
                                normalized_result.location_name
                            ),
                            title=item.title,
                            published_at=(
                                item.published_at
                            ),
                        )
                    )

                created_new_event = False

                if existing_event_id is None:

                    existing_event_id = (
                        event_store.create_event(
                            category=(
                                normalized_result.category.value
                            ),
                            location_name=(
                                normalized_result.location_name
                            ),
                            primary_title=(
                                item.title
                            ),
                            confidence=(
                                normalized_result.confidence
                            ),
                            latitude=(
                                event.location.latitude
                                if not (
                                    event.location.latitude == 0.0
                                    and event.location.longitude == 0.0
                                )
                                else None
                            ),
                            longitude=(
                                event.location.longitude
                                if not (
                                    event.location.latitude == 0.0
                                    and event.location.longitude == 0.0
                                )
                                else None
                            ),
                        )
                    )

                    created_new_event = True

                    print(
                        "  NEW EVENT CREATED"
                    )

                elif found_by_evidence_url:

                    print(
                        "  EXISTING EVENT FOUND "
                        "BY EVIDENCE URL"
                    )

                else:

                    print(
                        "  EXISTING EVENT FOUND "
                        "BY EVENT MATCHER"
                    )

                if not (
                    event.location.latitude == 0.0
                    and event.location.longitude == 0.0
                ):
                    event_store.set_event_coordinates(
                        event_id=existing_event_id,
                        latitude=event.location.latitude,
                        longitude=event.location.longitude,
                    )

                existing_evidence_id = (
                    event_store.find_existing_evidence_id(
                        event_id=existing_event_id,
                        source=item.source,
                        title=item.title,
                        url=item_url,
                    )
                )

                evidence_id = (
                    event_store.add_evidence(
                        event_id=existing_event_id,
                        source=item.source,
                        title=item.title,
                        url=item_url,
                        published_at=(
                            item.published_at
                        ),
                        confidence=(
                            normalized_result.confidence
                        ),
                        reason=(
                            normalized_result.reason
                        ),
                    )
                )

                print(
                    f"  Event ID: "
                    f"{existing_event_id}"
                )

                if existing_evidence_id is None:

                    print(
                        "  Evidence added: 1"
                    )

                else:

                    print(
                        "  Evidence already exists; "
                        "reused existing record."
                    )

                apply_event_lifecycle(
                    event_store=event_store,
                    event_id=existing_event_id,
                    item=item,
                    evidence_id=evidence_id,
                )

            elif (
                gate_decision.action
                == EventGateAction.attach_follow_up
            ):

                print()
                print("EVENT STORE FOLLOW-UP")

                if (
                    normalized_result.category is None
                    or not normalized_result.location_name
                ):

                    print(
                        "  Follow-up cannot be attached: "
                        "category or location is missing."
                    )

                else:

                    item_url = getattr(
                        item,
                        "url",
                        None,
                    )

                    existing_event_id = (
                        event_store.find_event_by_evidence_url(
                            item_url
                        )
                    )

                    found_by_evidence_url = (
                        existing_event_id is not None
                    )

                    if existing_event_id is None:

                        existing_event_id = (
                            event_store.find_matching_event(
                                category=(
                                    normalized_result.category.value
                                ),
                                location_name=(
                                    normalized_result.location_name
                                ),
                                title=item.title,
                                published_at=(
                                    item.published_at
                                ),
                            )
                        )

                    # Follow-up headlines can differ strongly
                    # from the original incident headline.
                    # If semantic title matching fails, use
                    # the newest event with the same category
                    # and canonical location as a temporary
                    # conservative fallback.
                    if existing_event_id is None:

                        existing_event_id = (
                            event_store.find_matching_event(
                                category=(
                                    normalized_result.category.value
                                ),
                                location_name=(
                                    normalized_result.location_name
                                ),
                                published_at=(
                                    item.published_at
                                ),
                            )
                        )

                    if existing_event_id is None:

                        print(
                            "  NO EXISTING EVENT FOUND"
                        )

                    else:

                        follow_up_coordinates = (
                            resolve_coordinates(
                                normalized_result.location_name
                            )
                        )

                        if follow_up_coordinates is not None:
                            event_store.set_event_coordinates(
                                event_id=existing_event_id,
                                latitude=(
                                    follow_up_coordinates.latitude
                                ),
                                longitude=(
                                    follow_up_coordinates.longitude
                                ),
                            )

                        existing_evidence_id = (
                            event_store.find_existing_evidence_id(
                                event_id=existing_event_id,
                                source=item.source,
                                title=item.title,
                                url=item_url,
                            )
                        )

                        evidence_id = (
                            event_store.add_evidence(
                                event_id=existing_event_id,
                                source=item.source,
                                title=item.title,
                                url=item_url,
                                published_at=(
                                    item.published_at
                                ),
                                confidence=(
                                    normalized_result.confidence
                                ),
                                reason=(
                                    normalized_result.reason
                                ),
                            )
                        )

                        if found_by_evidence_url:

                            print(
                                "  FOLLOW-UP REUSED "
                                "EXISTING EVENT BY URL"
                            )

                        else:

                            print(
                                "  FOLLOW-UP ATTACHED"
                            )

                        print(
                            f"  Event ID: "
                            f"{existing_event_id}"
                        )

                        if existing_evidence_id is None:

                            print(
                                "  Evidence added: 1"
                            )

                        else:

                            print(
                                "  Evidence already exists; "
                                "reused existing record."
                            )

                        apply_event_lifecycle(
                            event_store=event_store,
                            event_id=existing_event_id,
                            item=item,
                            evidence_id=evidence_id,
                        )

        except Exception as error:

            print("LLM ERROR")

            print(
                f"  {type(error).__name__}: "
                f"{error}"
            )

        print()
        print("-" * 80)
        print()

    # --------------------------------------------------
    # Event Correlation
    # --------------------------------------------------

    print()
    print("=" * 80)
    print()
    print("EVENT CORRELATION")

    if event_candidates:

        clusters = cluster_event_candidates(
            event_candidates
        )

        for number, cluster in enumerate(
            clusters,
            start=1,
        ):

            first = cluster[0].classification

            print()
            print(
                f"Cluster #{number}"
            )

            print(
                f"  Category: "
                f"{first.category}"
            )

            print(
                f"  Location: "
                f"{first.location_name}"
            )

            print(
                f"  Evidence count: "
                f"{len(cluster)}"
            )

            for evidence in cluster:

                print(
                    f"    - {evidence.item.source}: "
                    f"{evidence.item.title}"
                )

    else:

        print(
            "No created events to correlate."
        )


if __name__ == "__main__":
    main()
