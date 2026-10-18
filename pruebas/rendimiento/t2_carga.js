// T2 - Semana 9: evaluación básica NO destructiva sobre servidor local de pruebas.
// No ejecutar contra servidores ajenos o de producción.
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = (__ENV.BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

export const options = {
  stages: [
    { duration: '5s', target: 2 },
    { duration: '15s', target: 5 },
    { duration: '5s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<2000'],
    checks: ['rate>0.95'],
  },
  tags: { prueba: 'T2-semana9', proyecto: 'Talenvia' },
};

export default function () {
  const rutas = ['/', '/ofertas/', '/ofertas/?modalidad=REMOTO', '/ofertas/?q=Analista'];
  const ruta = rutas[(__ITER + __VU) % rutas.length];
  const respuesta = http.get(BASE_URL + ruta, { timeout: '10s' });
  check(respuesta, {
    'HTTP 200': (r) => r.status === 200,
    'pagina Talenvia': (r) => r.body.includes('Talenvía'),
  });
  sleep(0.5);
}
