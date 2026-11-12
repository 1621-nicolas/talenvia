import http from 'k6/http';
import { check } from 'k6';
import { Rate } from 'k6/metrics';

const aTiempo = new Rate('busqueda_valida_en_2s');
export const options = {
  scenarios: { muestra: {executor: 'shared-iterations', vus: 1, iterations: 20, maxDuration: '2m'} },
  thresholds: { busqueda_valida_en_2s: ['rate>=0.95'], checks: ['rate==1'] },
};
export default function () {
  const ruta = '/ofertas/?q=Analista&pagina=' + (1 + __ITER % 5);
  const r = http.get('http://127.0.0.1:8000' + ruta);
  const valida = check(r, { 'resultados de la búsqueda': s => s.status === 200 && s.body.includes('tarjeta-enlace') });
  aTiempo.add(valida && r.timings.duration <= 2000);
}
