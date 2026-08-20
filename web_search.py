from ddgs import DDGS


def search_web(query, max_results=5):

    try:

        print(f"\n🌐 Searching web for: {query}")

        results = DDGS(
            timeout=10
        ).text(
            query=query,
            region="in-en",
            safesearch="moderate",
            max_results=max_results
        )

        if not results:
            return None

        formatted_results = []

        for index, result in enumerate(results, start=1):

            title = result.get(
                "title",
                "No title"
            )

            body = result.get(
                "body",
                ""
            )

            url = result.get(
                "href",
                ""
            )

            formatted_results.append(
                f"""
Result {index}
Title: {title}
Information: {body}
Source: {url}
"""
            )

        return "\n".join(
            formatted_results
        )

    except Exception as error:

        print(
            f"Web search error: {error}"
        )

        return None


if __name__ == "__main__":

    data = search_web(
        "latest artificial intelligence news"
    )

    print(data)