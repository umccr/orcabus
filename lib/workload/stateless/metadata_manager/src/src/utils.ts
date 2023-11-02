import axios from 'axios';

/**
 * Use the default lambda layer extension to query secret manager
 * @param secretManagerName The name of the secret or ARN
 * @returns
 */
export const getSecretManagerWithLayerExtension = async (secretManagerName: string) => {
  const apiUrl = `http://localhost:2773/secretsmanager/get?secretId=${encodeURIComponent(
    secretManagerName
  )}`;
  const headers = { 'X-Aws-Parameters-Secrets-Token': process.env.AWS_SESSION_TOKEN };
  const res = await axios.get(apiUrl, {
    headers: headers,
  });

  return res.data.SecretString;
};

/**
 * Use the default lambda layer extension to query system parameter store (WITH decryption)
 * @param parameterStoreName The name of the parameterStore or ARN
 * @returns
 */
export const getParameterDecryptedStoreWithLayerExtension = async (parameterStoreName: string) => {
  const apiUrl = `http://localhost:2773/systemsmanager/parameters/get/?name=${encodeURIComponent(
    parameterStoreName
  )}&withDecryption=true`;

  const headers = { 'X-Aws-Parameters-Secrets-Token': process.env.AWS_SESSION_TOKEN };
  const res = await axios.get(apiUrl, {
    headers: headers,
  });

  return res.data.Parameter.Value;
};
