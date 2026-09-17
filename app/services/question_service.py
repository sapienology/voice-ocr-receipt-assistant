
class QuestionService:

    def answer(self, question, receipt):

        question = question.lower().strip()

        # -----------------------------
        # TOTAL
        # -----------------------------

        if "total" in question:

            if receipt.total is not None:

                return f"The total amount is {receipt.total:.2f}."

            return "I could not find the total amount on the receipt."

        # -----------------------------
        # MERCHANT
        # -----------------------------

        if (
            "merchant" in question
            or "store" in question
            or "shop" in question
            or "seller" in question
            or "who sold" in question
        ):

            if receipt.merchant:

                return f"The merchant is {receipt.merchant}."

            return "I could not find the merchant name."

        # -----------------------------
        # DATE
        # -----------------------------

        if "date" in question or "when" in question:

            if receipt.date:

                return f"The receipt date is {receipt.date}."

            return "I could not find the receipt date."

        # -----------------------------
        # INVOICE NUMBER
        # -----------------------------

        if (
            "invoice number" in question
            or "invoice no" in question
            or "invoice id" in question
        ):

            if receipt.invoice_number:

                return (
                    f"The invoice number is "
                    f"{receipt.invoice_number}."
                )

            return "I could not find the invoice number."

        # -----------------------------
        # SUBTOTAL
        # -----------------------------

        if "subtotal" in question:

            if receipt.subtotal is not None:

                return (
                    f"The subtotal is "
                    f"{receipt.subtotal:.2f}."
                )

            return "I could not find the subtotal."

        # -----------------------------
        # TAX / VAT
        # -----------------------------

        if "tax" in question or "vat" in question:

            if receipt.tax is not None:

                return f"The tax amount is {receipt.tax:.2f}."

            return "I could not find the tax amount."

        # -----------------------------
        # ITEMS
        # -----------------------------

        if (
            "items" in question
            or "bought" in question
            or "purchased" in question
        ):

            if receipt.items:

                item_names = [
                    item.name
                    for item in receipt.items
                ]

                return (
                    "The receipt contains: "
                    + ", ".join(item_names)
                    + "."
                )

            return "I could not find the items."

        # -----------------------------
        # UNKNOWN QUESTION
        # -----------------------------

        return (
            "I am sorry, I do not understand "
            "that question yet."
        )