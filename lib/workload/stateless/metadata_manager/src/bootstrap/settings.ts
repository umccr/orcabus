export type SettingType = {
  port: number;
  host: string;
};

export default function getAppSettings(): SettingType {
  const isDevelopment = process.env.NODE_ENV === 'development';

  if (isDevelopment) {
    return {
      port: parseInt(process.env.PORT ?? '8080'),
      host: process.env.HOST ?? 'localhost',
    };
  } else {
    throw new Error('App is not ready for production');
  }
}
