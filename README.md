# Welcome to Steph's Technical Challenge App!

In this repo you'll find my Technical Challenge project for WorkOS, which demonstrates WorkOS' SSO and Directory Sync features.

These instructions will walk you through downloading my app and running it locally.

## Clone the repo

First, you'll want to either fork or clone my repo. You can fork using [these instructions](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) or clone using [these instructions](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository#cloning-a-repository).

## Create a WorkOS account

Before you start working with the app, you'll need to create a few accounts, starting with a free WorkOS account.

1. Go to workos.com.
2. Click the **Get Started** button and follow the prompts to create your account.
3. Click on **Organizations** in the left sidebar, then the **Create organization** button.
4. Fill out the information, then click **Create organization** when you're done.
5. In your new organization page, find the Organization ID under your org name and copy it (should be in the format `org_...`). You'll need this later for `.env` file in the app.

## Set up SSO in WorkOS

1. Follow [these instructions](https://workos.com/docs/sso) to create an SSO connection for your new organization.
2. Click on **Overview** to go to your WorkOS dashboard, then under **Copy environment variables**, copy your:
   1.  `WORKOS_CLIENT_ID` (should be in the format `client_...`), and
   2.  `WORKOS_API_KEY` (should be in the format `sk_test_...`).
       1. You'll need these later for `.env` file in the app.
3. Lastly, click on **Redirects** in the left side bar and add `http://localhost:8000/auth/callback` as an allowed **Redirect URI**. This is the default callback URI that the app uses.

I recommend keeping your WorkOS organization page open in your browser, as it has information you'll need to set up your Okta account later.

## Create an Okta account & set up SAML 2.0 app

1. This app uses Okta as its IdP, so the next step is to create an [Okta Integrator Free account](https://developer.okta.com/signup/).
2. Follow [these instructions](https://workos.com/docs/integrations/okta-saml) to create an Okta SAML 2.0 app.
   1. When you're asked for the **Single sign on URL** and **Audience URI (SP Entity ID)**, go back to your WorkOS organization's Connection page, copy the ACS URL, and paste into the Single sign-on field in Okta. Repeat for the Audience URI (SP Entity ID) field in Okta.
   2. Follow the instructions above to connect your Okta SAML 2.0 app to WorkOS.

## Set up Directory Sync (SCIM) in WorkOS and Okta

My app is also set up to automatically provision users in my organization via Okta SCIM, so you'll need to set up Directory Sync in WorkOS and create a SCIM application in Okta.

Rather than go into detail here, I recommend using [WorkOS's doc for setting up Okta SCIM](https://workos.com/docs/integrations/okta-scim), as it offers detailed, step by step instructions for setting up and configuring Directory Sync for your organization.

### Map data in WorkOS and Okta

Once you've set up Directory Sync in both WorkOS and Okta, you'll need to ensure data is mapped correctly in WorkOS and Okta.

**In Okta:**
1. Go to **Admin Console > Application > Applications > Your SAML app > Sign On tab > Settings section** and click **Edit**.
2. Scroll down to the **Attribute statements** section, click the **Show legacy configuration** dropdown menu.
3. In the **Profile attribute statements** section, click **Edit** and add these attribute statements:

| Name      | Name format | Value          |
| --------- | ----------- | -------------- |
| email     | Unspecified | user.login     |
| firstName | Unspecified | user.firstName |
| lastName  | Unspecified | user.lastName  |

**NOTE:** If there's an option to do this, make sure that each attribute's Value type is set to **Expression**, not the default **Basic**.

5. Click **Save**.

**In WorkOS:**

1. Go to **Organizations > your organization**.
2. In the **Single Sign-On** section, click **View connection**.
3. Scroll down to the **Attribute mapping** section and click **Edit attribute mapping**.
4. Map the attributes as follows:

| Attribute name | IdP field name |
| -------------- | -------------- |
| email          | userName       |
| firstName      | firstName      |
| idpid          | NameID         |
| lastName       | lastName       |
| username       | userName       |

5. Click **Save changes**.

## Configure the app

Now that you've set up your WorkOS organization and Okta SAML 2.0 and SCIM apps, it's time to add the IDs and keys you saved earlier as environment variables in the `.env` file so that the app can retrieve and display your information.

1. Open the project in your code editor of choice.
2. Copy `.env.example` to a new file named `.env`.
3. Replace the dummy values in the file with your values.

```
DJANGO_SECRET_KEY=<generate a secret key — see tip below>
WORKOS_CLIENT_ID=<your WorkOS client ID>
WORKOS_API_KEY=<your WorkOS API key>
DEBUG=False
REDIRECT_URI=http://localhost:8000/auth/callback
CUSTOMER_ORGANIZATION_ID=<your WorkOS organization ID>
```

You'll notice that there's a variable for DJANGO_SECRET_KEY. Rather than expose this in the code files, I elected to pass this as a secret in the `.env` file.

Here's how to generate a Django secret key in your terminal:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```
Add the Django secret key in the `.env` file, and be sure to save your changes.

## Run the app locally

Now we're ready to run the app!

First, open a terminal and navigate into the app directory:

`cd <path-to-repo>/python-django-sso-example`

Next, create and activate a virtual environment:

`python3 -m venv venv`

`source venv/bin/activate`

Install the dependencies needed to run the app:

`pip install -r requirements.txt`

(Try `pip3` if `pip` doesn't work.)

Set up the app database and collect static files:

`python3 manage.py migrate`

`python3 manage.py collectstatic`

Because we're serving up static files, we have to add `--insecure` when we're starting the server:

`python3 manage.py runserver --insecure`

We're ready to run the app!

Go to `http://localhost:8000` in your browser and click **Enterprise SAML** to log in.

You'll be directed to log into Okta first, and then you'll see the logged-in page where you should see your first and last name, your SSO details, and your Okta Directory, where you can click in to see your Users and Groups.

## Common errors & how to fix them

`Error: Unable to extract valid email address from profile.`

This means that either Okta isn't sending a valid email address in their SSO response or WorkOS isn't mapping that attribute correctly (or both).

To fix this, go to back to the **Map Data in WorkOS and Okta** step and make sure 1) you've added the attribute statements in Okta and 2) you've mapped the attributes in WorkOS.

`Error: The SAML Response did not contain expected attributes.`

Basically the same cause as the error above. To fix this, go to back to the **Map Data in WorkOS and Okta** step and make sure 1) you've added the attribute statements in Okta and 2) you've mapped the attributes in WorkOS.

`Error: Profile does not belong to the target Organization. The domain 'yourdomain.com' does not match any of the Organization's domains.`

This means that you haven't set a domain in WorkOS. To fix this:

1. Go to **WorkOS Dashboard > Organizations > your organization**.
2. Find the **Domains** section.
3. Add your email domain as a domain (everything after the @ in example@yourdomain.com).
4. Save your changes.

`App UI is broken / Images are broken`

This means that the static files with UI elements aren't being served.

To fix this:

1. Exit the server and run `python3 manage.py collectstatic`, or if you've done that,
2. Make sure you've included `--insecure` in your `runserver` command: `python3 manage.py runserver --insecure`.
