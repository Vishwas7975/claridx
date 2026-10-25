const wt = require('node:worker_threads')
if (!wt.markAsUncloneable) {
  wt.markAsUncloneable = (obj) => obj
}

if (!Promise.withResolvers) {
  Promise.withResolvers = function () {
    let resolve, reject
    const promise = new Promise((res, rej) => {
      resolve = res
      reject = rej
    })
    return { promise, resolve, reject }
  }
}

class BaseIterator {
  [Symbol.iterator]() {
    return this
  }
  find(predicate) {
    for (const item of this) {
      if (predicate(item)) return item
    }
    return undefined
  }
  filter(predicate) {
    const self = this
    return (function* () {
      for (const item of self) {
        if (predicate(item)) yield item
      }
    })()
  }
  map(fn) {
    const self = this
    return (function* () {
      for (const item of self) {
        yield fn(item)
      }
    })()
  }
  some(predicate) {
    for (const item of this) {
      if (predicate(item)) return true
    }
    return false
  }
  every(predicate) {
    for (const item of this) {
      if (!predicate(item)) return false
    }
    return true
  }
  toArray() {
    return [...this]
  }
  forEach(fn) {
    for (const item of this) {
      fn(item)
    }
  }
}

if (typeof globalThis.Iterator === 'undefined') {
  globalThis.Iterator = BaseIterator
} else {
  for (const method of ['find', 'filter', 'map', 'some', 'every', 'toArray', 'forEach']) {
    if (typeof globalThis.Iterator.prototype[method] !== 'function') {
      globalThis.Iterator.prototype[method] = BaseIterator.prototype[method]
    }
  }
}

const vm = require('node:vm')
const originalCreateContext = vm.createContext
vm.createContext = function (sandbox, options) {
  const ctx = originalCreateContext.call(this, sandbox, options)
  try {
    vm.runInContext(
      `
      ${BaseIterator.toString()}
      if (typeof Iterator === "undefined") {
        globalThis.Iterator = BaseIterator;
      } else {
        for (const method of ['find', 'filter', 'map', 'some', 'every', 'toArray', 'forEach']) {
          if (typeof Iterator.prototype[method] !== 'function') {
            Iterator.prototype[method] = BaseIterator.prototype[method];
          }
        }
      }
      if (!Promise.withResolvers) {
        Promise.withResolvers = function () {
          let resolve, reject;
          const promise = new Promise((res, rej) => {
            resolve = res;
            reject = rej;
          });
          return { promise, resolve, reject };
        };
      }
      `,
      ctx,
    )
  } catch (_) {}
  return ctx
}
