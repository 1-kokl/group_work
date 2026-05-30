/* eslint-disable */
/* tslint:disable */

const INTEGRITY_CHECKSUM = '90d27cbeb72c39c427fd63f6396866c4'
const bypassHeaderName = 'x-msw-bypass'
const activeClientIds = new Set()

self.addEventListener('install', function () {
  return self.skipWaiting()
})

self.addEventListener('activate', async function (event) {
  return self.clients.claim()
})

self.addEventListener('message', async function (event) {
  const clientId = event.source.id

  if (!clientId || !self.clients) {
    return
  }

  const client = await self.clients.get(clientId)

  if (!client) {
    return
  }

  const allClients = await self.clients.matchAll({
    type: 'window',
  })

  switch (event.data) {
    case 'KEEPALIVE_REQUEST': {
      sendToClient(client, {
        type: 'KEEPALIVE_RESPONSE',
      })
      break
    }

    case 'INTEGRITY_CHECK_REQUEST': {
      sendToClient(client, {
        type: 'INTEGRITY_CHECK_RESPONSE',
        payload: INTEGRITY_CHECKSUM,
      })
      break
    }

    case 'MOCK_ACTIVATE': {
      activeClientIds.add(clientId)

      sendToClient(client, {
        type: 'MOCKING_ENABLED',
        payload: true,
      })
      break
    }

    case 'MOCK_DEACTIVATE': {
      activeClientIds.delete(clientId)
      break
    }

    case 'CLIENT_CLOSED': {
      activeClientIds.delete(clientId)

      const remainingClients = allClients.filter((client) => {
        return client.id !== clientId
      })

      if (remainingClients.length === 0) {
        activeClientIds.clear()
      }

      break
    }
  }
})

self.addEventListener('fetch', function (event) {
  const { request } = event
  const accept = request.headers.get('accept') || ''

  if (accept.includes('text/event-stream')) {
    return
  }

  if (request.headers.get(bypassHeaderName) === 'true') {
    return
  }

  if (!activeClientIds.size) {
    return
  }

  const requestId = crypto.randomUUID()
  event.respondWith(
    handleRequest(event, requestId).catch((error) => {
      if (error.name === 'NetworkError') {
        console.warn(
          '[MSW] Successfully emulated a network error for the "%s %s" request.',
          request.method,
          request.url,
        )
        return
      }

      throw error
    }),
  )
})

async function handleRequest(event, requestId) {
  const client = await resolveMainClient(event)
  const response = await getResponse(event, client, requestId)

  if (!response) {
    return await fetch(event.request)
  }

  const responseClone = response.clone()

  sendToClient(client, {
    type: 'RESPONSE',
    payload: {
      requestId,
      isMockedResponse: true,
      status: responseClone.status,
      statusText: responseClone.statusText,
      body: responseClone.body ? await responseClone.text() : null,
      headers: Object.fromEntries(responseClone.headers.entries()),
      redirected: responseClone.redirected,
    },
  })

  return response
}

async function getResponse(event, client, requestId) {
  const { request } = event
  const clonedRequest = request.clone()

  function passthrough() {
    const headers = Object.fromEntries(clonedRequest.headers.entries())

    if (request.mode === 'navigate') {
      return
    }

    if (request.mode === 'cors') {
      headers['access-control-request-method'] = request.method
      headers['access-control-request-headers'] = clonedRequest.headers.get(
        'access-control-request-headers',
      ) || ''
    }

    return fetch(clonedRequest, { headers })
  }

  const clientMessage = await sendToClient(client, {
    type: 'REQUEST',
    payload: {
      id: requestId,
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(clonedRequest.headers.entries()),
      cache: request.cache,
      mode: request.mode,
      credentials: request.credentials,
      destination: request.destination,
      integrity: request.integrity,
      redirect: request.redirect,
      referrer: request.referrer,
      referrerPolicy: request.referrerPolicy,
      body: await request.text(),
      bodyUsed: request.bodyUsed,
      keepalive: request.keepalive,
    },
  })

  switch (clientMessage.type) {
    case 'MOCK_SUCCESS': {
      return new Response(clientMessage.payload.body, {
        ...clientMessage.payload,
        headers: clientMessage.payload.headers,
      })
    }

    case 'MOCK_NOT_FOUND': {
      return passthrough()
    }

    case 'NETWORK_ERROR': {
      const { name, message } = clientMessage.payload
      const networkError = new Error(message)
      networkError.name = name

      throw networkError
    }

    case 'INTERNAL_ERROR': {
      const parsedBody = JSON.parse(clientMessage.payload.body)

      console.error(
        '[MSW] Uncaught exception in the request handler for "%s %s":\n\n%s\n\n%s',
        request.method,
        request.url,
        parsedBody.message,
        parsedBody.stack,
      )

      return new Response(null, {
        status: 500,
        statusText: 'Request handler execution error',
      })
    }
  }

  return passthrough()
}

function sendToClient(client, message) {
  return new Promise((resolve, reject) => {
    const channel = new MessageChannel()

    channel.port1.onmessage = (event) => {
      if (event.data && event.data.error) {
        reject(event.data.error)
      } else {
        resolve(event.data)
      }
    }

    client.postMessage(message, [channel.port2])
  })
}

async function resolveMainClient(event) {
  const client = await self.clients.get(event.clientId)

  if (client?.frameType === 'top-level') {
    return client
  }

  const allClients = await self.clients.matchAll({
    type: 'window',
  })

  return allClients
    .filter((client) => {
      return client.visibilityState === 'visible'
    })
    .find((client) => {
      return activeClientIds.has(client.id)
    })
}

