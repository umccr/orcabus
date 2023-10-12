import axios from 'axios';

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

export const getParameterStoreWithLayerExtension = async (parameterStoreName: string) => {
  const apiUrl = `http://localhost:2773/systemsmanager/parameters/get/?name=${encodeURIComponent(
    parameterStoreName
  )}`;
  const headers = { 'X-Aws-Parameters-Secrets-Token': process.env.AWS_SESSION_TOKEN };
  const res = await axios.get(apiUrl, {
    headers: headers,
  });
  return res.data.Parameter.Value;
};
