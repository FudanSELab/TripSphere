/**
 * Util function to create protobuf Request object from JSON object
 * Since the generated protobuf code does not have a direct fromObject method,
 * this function provides a generic way to create a Request object from a JSON object
 *
 * @param MessageClass - protobuf message class (e.g. LoginRequest)
 * @param data - JSON object, field names should match AsObject type
 * @returns created protobuf message instance
 */
export function createRequestFromObject<T extends { [key: string]: any }>(
  MessageClass: new () => T,
  data: Partial<Record<string, any>>,
): T {
  const message = new MessageClass();
  // Iterate over each field of the data object
  for (const [key, value] of Object.entries(data)) {
    if (value === undefined || value === null) {
      continue;
    }

    // call the corresponding setter method according to the field name
    // for example: username -> setUsername, oldPassword -> setOldPassword
    const setterName = `set${key.charAt(0).toUpperCase()}${key.slice(1)}`;
    const setter = (message as any)[setterName];

    if (typeof setter === "function") {
      setter.call(message, value);
    }
  }

  return message;
}
