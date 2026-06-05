import { Configuration, RedirectRequest } from "@azure/msal-browser";

const azureClientId = process.env.REACT_APP_AZURE_CLIENT_ID;
const azureTenantId = process.env.REACT_APP_AZURE_TENANT_ID;

if (!azureClientId) {
    throw new Error("Missing environment variable: REACT_APP_AZURE_CLIENT_ID");
}

if (!azureTenantId) {
    throw new Error("Missing environment variable: REACT_APP_AZURE_TENANT_ID");
}

export const msalConfig: Configuration = {
    auth: {
        clientId: azureClientId,
        authority: `https://login.microsoftonline.com/${azureTenantId}`,
        redirectUri: window.location.origin,
        postLogoutRedirectUri: window.location.origin,
    },
    cache: {
        cacheLocation: "sessionStorage",
    },
};

export const loginRequest: RedirectRequest = {
    scopes: [`api://${azureClientId}/access`],
};

export const API_BASE_URL =
    process.env.REACT_APP_API_URL;