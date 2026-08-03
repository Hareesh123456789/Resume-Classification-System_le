from utils.knowledge_loader import (
    KnowledgeBaseError,
    build_skill_index,
    get_available_categories,
    load_all_skills,
    load_skill_category,
)


def main() -> None:

    try:
        knowledge_base = load_all_skills()

        print("=" * 70)
        print("KNOWLEDGE BASE LOADED SUCCESSFULLY")
        print("=" * 70)

        categories = get_available_categories()

        total_skills = 0

        for category in categories:

            category_skills = knowledge_base[category]
            total_skills += len(category_skills)

            print(
                f"{category:<25} "
                f"{len(category_skills):>4} skills"
            )

        print("-" * 70)
        print(f"Total categories: {len(categories)}")
        print(f"Total skill entries: {total_skills}")

        print("\nDATABASE TEST")
        print("-" * 70)

        databases = load_skill_category("databases")

        print(f"Database skills loaded: {len(databases)}")
        print(f"Oracle found: {'Oracle' in databases}")
        print(f"MongoDB found: {'MongoDB' in databases}")

        print("\nSEARCH INDEX TEST")
        print("-" * 70)

        skill_index = build_skill_index()

        for skill in [
            "python",
            "oracle",
            "html",
            "docker",
            "raspberry pi",
        ]:
            print(
                f"{skill}: "
                f"{skill_index.get(skill, [])}"
            )

    except (
        KnowledgeBaseError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:

        print("\nKNOWLEDGE BASE ERROR")
        print("-" * 70)
        print(error)


if __name__ == "__main__":
    main()