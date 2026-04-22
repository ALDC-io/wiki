---
tags: [entity, tool, windsor, marketing, data-aggregation, fusion92]
aliases: [Windsor, Windsor.ai]
sources: [CF92/1675001857, CF92/1675919361]
created: 2026-04-18
updated: 2026-04-18
---

# Windsor

Windsor.ai is a marketing data aggregation platform used by [[fusion92]]. It connects to ad platforms (Facebook Ads, Google Ads, etc.) and exposes a unified data feed that [[Eclipse]] pulls from via the `windsor` connection in the Fusion92 client config.

## Authentication & Platform Setup

### Adding Users

Team members must be added in Windsor under the **Manage Account** screen. The initial user is invited by ALDC; subsequent users can be invited by either ALDC or the Fusion92 team.

An invitation email is sent and must be accepted before access is active.

### Granting a Platform Access to Windsor

Example: Facebook Ads.

1. Log into Windsor.
2. Select **Facebook Ads** on the sidebar.
3. Click **Grant Facebook Ads Access**:
   - A Facebook authentication popup opens.
   - **Log in as the user who has ad access to the desired accounts.** This is required — the authenticating user must have permissions to the account data you want Windsor to pull.
   - Edit permissions in the Facebook dialog:
     - Enable: "Access your Page and App Insights" and "Access your Facebook ads and related stats".
     - Disable all other sliders.
     - Leave the permissions box.
   - Continue through any remaining Facebook steps.
4. Once connected, Windsor shows a list of available ad accounts.
5. Tick the box next to each account that should be synced.

## Adding Accounts to Platform Connections

After Windsor is authenticated for a platform, any team member with Windsor access can adjust which accounts Eclipse is authorized to pull data for.

### Managing Accounts

Under **Manage Account**, new users can be added at any time. Once invited and accepted, they can see and toggle accounts across all connected platforms.

To authorize an account: simply tick the box next to the account name in the relevant platform view.

### Troubleshooting: Missing Accounts

If an expected account does not appear in Windsor's account list, the likely causes are:

- The permissions for the authenticating user need adjusting (they lack ad access to that account in the platform).
- Windsor was authenticated with a user who does not have access to the missing account — re-authenticate with a user who does.

## See Also

- [[fusion92]] — client using Windsor; `windsor` Eclipse connection
- [[Eclipse]] — pulls data from Windsor
