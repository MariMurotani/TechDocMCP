class ContentPolicy:
    """
    Encapsulates heuristics to decide whether extracted text is meaningful.
    Allows domain/category-specific adjustments.
    """

    def __init__(self, aws_cdk_domain: str = "docs.aws.amazon.com"):
        self.aws_cdk_domain = aws_cdk_domain

    def is_meaningful(self, text: str) -> bool:
        if not text or len(text.strip()) < 200:
            return False
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        if len(lines) < 10:
            return False
        avg_line_length = sum(len(line) for line in lines) / len(lines)
        if avg_line_length < 25:
            return False
        word_count = len(text.split())
        if word_count < 50:
            return False
        return True

    def is_meaningful_for(self, path: str, text: str) -> bool:
        is_aws_cdk_page = (self.aws_cdk_domain in path and 
                            "/cdk/" in path.lower())
        if is_aws_cdk_page:
            if not text or len(text.strip()) < 120:
                return False
            lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
            if len(lines) < 6:
                return False
            avg_line_length = sum(len(line) for line in lines) / len(lines)
            if avg_line_length < 18:
                return False
            word_count = len(text.split())
            if word_count < 35:
                return False
            return True
        return self.is_meaningful(text)
