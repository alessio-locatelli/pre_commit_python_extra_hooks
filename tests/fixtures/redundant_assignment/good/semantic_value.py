"""Test semantic value preservation - should NOT be flagged."""


def example1():
    # Should NOT flag: transformative verb adds meaning
    formatted_timestamp = format_iso8601(raw_ts)
    return formatted_timestamp


def example2():
    # Should NOT flag: complex expression, name adds clarity
    user_full_name = f"{user.first_name} {user.last_name}"
    send_email(recipient=user_full_name)


def example3():
    # Should NOT flag: breaking long expression
    discount_rate = calculate_discount(
        cart_total, customer_status, promo_code, region
    )
    return discount_rate


def example4():
    # Should NOT flag: multiple uses
    value = expensive_calc()
    print(value)
    log(value)
    return value
