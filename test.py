import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        pdf_url = fetch_latest_pdf()
        logging.info(f"Fetched PDF URL: {pdf_url}")
        json_output = parse_pdf_to_json(pdf_url)
        logging.info(f"Parsed JSON Output: {json_output}")
    except Exception as e:
        logging.error(f"Error: {e}")