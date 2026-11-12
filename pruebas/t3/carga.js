// Perfiles acotados para una instancia efímera de CI en loopback.
import http from 'k6/http';
import { check, sleep } from 'k6';

const perfiles = {
  carga: [{ duration: '10s', target: 5 }, { duration: '30s', target: 5 }, { duration: '5s', target: 0 }],
  escalones: [5, 10, 20, 30, 0].map(target => ({ duration: '15s', target })),
  pico: [2, 25, 2, 0].map(target => ({ duration: '12s', target })),
  resistencia: [{ duration: '5s', target: 5 }, { duration: '3m', target: 5 }, { duration: '5s', target: 0 }],
};
const perfil = __ENV.PERFIL || 'carga';
if (!perfiles[perfil]) throw new Error('Perfil desconocido');
export const options = {
  stages: perfiles[perfil],
  thresholds: { http_req_failed: ['rate<0.01'], http_req_duration: ['p(95)<2000'], checks: ['rate==1'] },
  tags: { perfil },
};
export default function () {
  const rutas = ['/ofertas/', '/ofertas/?q=Analista', '/ofertas/?modalidad=REMOTO', '/'];
  const res = http.get('http://127.0.0.1:8000' + rutas[(__ITER + __VU) % rutas.length], { timeout: '10s' });
  check(res, { 'HTTP 200': r => r.status === 200, 'contenido de Talenvía': r => r.body && r.body.includes('Talenvía') });
  sleep(0.5);
}
