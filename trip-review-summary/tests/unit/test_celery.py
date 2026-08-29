from review_summary.celery import create_celery_app


def test_celery_app_registers_index_workflow_tasks() -> None:
    celery_app = create_celery_app()
    celery_app.finalize(auto=True)

    expected_tasks = {
        "review_summary.index.tasks.collect_text_units.run_workflow",
        "review_summary.index.tasks.extract_graph.run_workflow",
        "review_summary.index.tasks.finalize_graph.run_workflow",
        "review_summary.index.tasks.create_communities.run_workflow",
        "review_summary.index.tasks.create_final_text_units.run_workflow",
        "review_summary.index.tasks.create_community_reports.run_workflow",
        "review_summary.index.tasks.create_text_embeddings.run_workflow",
    }

    assert expected_tasks <= set(celery_app.tasks)
