# Plans and store subscriptions

Platform administrators create and archive subscription plans. A plan has a stable code, display name, price in integer minor units, currency, billing interval, and a JSON limits map for future feature enforcement. Existing store subscriptions keep their selected plan if that plan is later archived, but merchants cannot newly select an archived plan.

Each store has at most one current subscription row. Owners and admins can select an active plan or cancel the current plan. Managers may view plan information; other store roles cannot access subscription routes. Platform admins can inspect all subscriptions and aggregate monthly recurring revenue by currency. Yearly plan prices are divided by twelve for this estimate.

These records are administrative state only. Payment collection, invoices, proration, renewals, taxes, and billing webhooks are not integrated. A payment provider should become the source of subscription status before the product charges merchants.
