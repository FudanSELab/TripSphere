
export function isSSR(): boolean {
  return typeof window === 'undefined'
}

export function isCSR(): boolean {
  return typeof window !== 'undefined'
}

export function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof document !== 'undefined'
}

export function getEnv(): 'ssr' | 'csr' {
  return typeof window === 'undefined' ? 'ssr' : 'csr'
}

