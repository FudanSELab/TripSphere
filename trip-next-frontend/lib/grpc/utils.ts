/**
 * 从 JSON 对象创建 protobuf Request 对象的辅助函数
 *
 * 由于生成的 protobuf 代码没有直接的 fromObject 方法，
 * 这个函数提供了一个通用的方式来从 JSON 对象创建 Request 对象
 *
 * @param MessageClass - protobuf 消息类（如 LoginRequest）
 * @param data - JSON 对象，字段名应该匹配 AsObject 类型
 * @returns 创建的 protobuf 消息实例
 *
 * @example
 * ```typescript
 * const jsonData = { username: 'test', password: '123456' }
 * const request = createRequestFromObject(LoginRequest, jsonData)
 * ```
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
