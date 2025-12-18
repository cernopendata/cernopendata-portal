const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/;

export const validateEmail = (email) => {
  if (!email) return false;
  return EMAIL_REGEX.test(email.trim());
};
