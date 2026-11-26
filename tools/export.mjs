import { writeFileSync } from 'node:fs'
import * as tax from '../../israel-tax/index.js'
import * as salary from '../../israel-tax/net-salary.js'
import * as selfEmployed from '../../israel-tax/self-employed-tax.js'
import * as purchase from '../../israel-tax/purchase-tax.js'
import * as severance from '../../israel-tax/severance-pay.js'
import * as credits from '../../israel-tax/tax-credit-points.js'
import * as recuperation from '../../israel-tax/recuperation-pay.js'
import * as minimum from '../../israel-tax/minimum-wage.js'

const [dataPath, fixturesPath] = process.argv.slice(2)

const snake = (name) => name.replace(/([a-z0-9])([A-Z])/g, '$1_$2').replace(/([A-Z])([A-Z][a-z])/g, '$1_$2').toLowerCase()

const snakeKeys = (value) => {
  if (Array.isArray(value)) return value.map(snakeKeys)
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([name, item]) => [snake(name), snakeKeys(item)]))
  }
  return value
}

const pyLiteral = (value) => {
  if (value === null || value === undefined) return 'None'
  if (value === true) return 'True'
  if (value === false) return 'False'
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : JSON.stringify(value)
  if (typeof value === 'string') return JSON.stringify(value)
  if (Array.isArray(value)) return `(${value.map(pyLiteral).join(', ')}${value.length === 1 ? ',' : ''})`
  return `{${Object.entries(value).map(([name, item]) => `${JSON.stringify(name)}: ${pyLiteral(item)}`).join(', ')}}`
}

const constants = {
  TAX_YEAR: selfEmployed.TAX_YEAR,
  MONTHS_IN_YEAR: selfEmployed.MONTHS_IN_YEAR,
  CREDIT_POINT_ANNUAL: selfEmployed.CREDIT_POINT_ANNUAL,
  DEFAULT_CREDIT_POINTS: selfEmployed.DEFAULT_CREDIT_POINTS,
  ANNUAL_TAX_BRACKETS: snakeKeys(selfEmployed.ANNUAL_TAX_BRACKETS),
  ANNUAL_SURTAX_THRESHOLD: selfEmployed.ANNUAL_SURTAX_THRESHOLD,
  SURTAX_RATE_BASIS_POINTS: selfEmployed.SURTAX_RATE_BASIS_POINTS,
  BTL_REDUCED_LIMIT_MONTHLY: selfEmployed.BTL_REDUCED_LIMIT_MONTHLY,
  BTL_MAX_INCOME_MONTHLY: selfEmployed.BTL_MAX_INCOME_MONTHLY,
  BTL_MIN_INCOME_MONTHLY: selfEmployed.BTL_MIN_INCOME_MONTHLY,
  BTL_SELF_EMPLOYED_RATES: selfEmployed.BTL_RATES,
  BTL_DEDUCTIBLE_BASIS_POINTS: selfEmployed.BTL_DEDUCTIBLE_BASIS_POINTS,
  BTL_EMPLOYEE_RATES: salary.BTL_EMPLOYEE_RATES,
  BTL_EMPLOYER_RATES: salary.BTL_EMPLOYER_RATES,
  PENSION_EMPLOYEE_BASIS_POINTS: salary.PENSION_EMPLOYEE_BASIS_POINTS,
  PENSION_EMPLOYER_BASIS_POINTS: salary.PENSION_EMPLOYER_BASIS_POINTS,
  SEVERANCE_BASIS_POINTS: salary.SEVERANCE_BASIS_POINTS,
  HISHTALMUT_EMPLOYEE_BASIS_POINTS: salary.HISHTALMUT_EMPLOYEE_BASIS_POINTS,
  HISHTALMUT_EMPLOYER_BASIS_POINTS: salary.HISHTALMUT_EMPLOYER_BASIS_POINTS,
  HISHTALMUT_SALARY_CEILING_MONTHLY: salary.HISHTALMUT_SALARY_CEILING_MONTHLY,
  PENSION_CREDIT_RATE_BASIS_POINTS: salary.PENSION_CREDIT_RATE_BASIS_POINTS,
  PENSION_CREDIT_SHARE_BASIS_POINTS: salary.PENSION_CREDIT_SHARE_BASIS_POINTS,
  PENSION_CREDIT_SALARY_CEILING_MONTHLY: salary.PENSION_CREDIT_SALARY_CEILING_MONTHLY,
  MAX_GROSS_MONTHLY: salary.MAX_GROSS_MONTHLY,
  STANDARD_VAT_RATE: tax.STANDARD_VAT_RATE,
  SINGLE_BRACKETS: snakeKeys(purchase.SINGLE_BRACKETS),
  ADDITIONAL_BRACKETS: snakeKeys(purchase.ADDITIONAL_BRACKETS),
  OLEH_BRACKETS: snakeKeys(purchase.OLEH_BRACKETS),
  OLEH_VALUE_CEILING: purchase.OLEH_VALUE_CEILING,
  EXEMPTION_CEILING_YEAR: severance.EXEMPTION_CEILING_YEAR,
  EXEMPTION_CEILING_PER_YEAR: severance.EXEMPTION_CEILING_PER_YEAR,
  MIN_SENIORITY_YEARS: severance.MIN_SENIORITY_YEARS,
  MAX_SALARY: severance.MAX_SALARY,
  POINT_VALUE_MONTHLY: credits.POINT_VALUE_MONTHLY,
  RESIDENT_TWELFTHS: credits.RESIDENT_TWELFTHS,
  COMMUTE_TWELFTHS: credits.COMMUTE_TWELFTHS,
  WOMAN_TWELFTHS: credits.WOMAN_TWELFTHS,
  CHILD_BANDS: credits.CHILD_BANDS.map(snake),
  CHILD_POINTS_TWELFTHS: snakeKeys(credits.CHILD_POINTS_TWELFTHS),
  OLEH_SCHEDULE: credits.OLEH_SCHEDULE,
  SOLDIER_MONTHS: credits.SOLDIER_MONTHS,
  SOLDIER_TWELFTHS_FULL: credits.SOLDIER_TWELFTHS_FULL,
  SOLDIER_TWELFTHS_SHORT: credits.SOLDIER_TWELFTHS_SHORT,
  DEGREE_TWELFTHS: credits.DEGREE_TWELFTHS,
  DAY_RATE_AGOROT: recuperation.DAY_RATE_AGOROT,
  PREVIOUS_RATE_AGOROT: recuperation.PREVIOUS_RATE_AGOROT,
  SENIORITY_TABLE: recuperation.seniorityTable,
  WAGE_PERIODS: snakeKeys(minimum.wagePeriods),
  CURRENT_PERIOD: minimum.CURRENT_PERIOD,
  YOUTH_HOURS_DIVISOR: minimum.YOUTH_HOURS_DIVISOR,
  AGE_GROUPS: minimum.ageGroups,
}

writeFileSync(
  dataPath,
  `${Object.entries(constants).map(([name, value]) => `${name} = ${pyLiteral(value)}`).join('\n')}\n`,
)

let seed = 20261126
const random = () => {
  seed = (seed + 0x6d2b79f5) | 0
  let t = seed
  t = Math.imul(t ^ (t >>> 15), t | 1)
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296
}
const between = (low, high) => low + Math.floor(random() * (high - low + 1))
const pick = (list) => list[Math.floor(random() * list.length)]
const cents = (low, high) => between(low * 100, high * 100) / 100

const around = (values) => [...new Set(values.flatMap((value) => [value - 1, value, value + 1]))].filter((value) => value >= 0)

const run = (call) => {
  try {
    return { result: snakeKeys(call()) }
  } catch (error) {
    return { error: error.message }
  }
}

const jsOptions = (kwargs) =>
  Object.fromEntries(
    Object.entries(kwargs)
      .filter(([, value]) => value !== undefined)
      .map(([name, value]) => [name.replace(/_([a-z0-9])/g, (_, letter) => letter.toUpperCase()), value]),
  )

const monthlyEdges = [
  ...selfEmployed.ANNUAL_TAX_BRACKETS.filter((bracket) => bracket.upTo !== null).map((bracket) => bracket.upTo / 12),
  selfEmployed.ANNUAL_SURTAX_THRESHOLD / 12,
  selfEmployed.BTL_REDUCED_LIMIT_MONTHLY,
  selfEmployed.BTL_MAX_INCOME_MONTHLY,
  salary.HISHTALMUT_SALARY_CEILING_MONTHLY,
  salary.PENSION_CREDIT_SALARY_CEILING_MONTHLY,
]

const salaryOptions = () => {
  const options = {}
  const points = pick([undefined, undefined, 0, 1, 2.25, 2.75, 3.5, 4.25, 7.333, 12])
  if (points !== undefined) options.credit_points = points
  options.gender = pick(['man', 'woman'])
  options.hishtalmut = pick([false, true])
  options.severance = pick(['partial', 'full'])
  return options
}

const netSalaryCases = [
  ...around(monthlyEdges).map((gross) => ({ gross, kwargs: salaryOptions() })),
  ...Array.from({ length: 180 }, () => ({ gross: pick([between(0, 30000), between(30000, 120000), cents(0, 40000)]), kwargs: salaryOptions() })),
  { gross: 0, kwargs: {} },
  { gross: 15000, kwargs: {} },
  { gross: 15000, kwargs: { gender: 'woman' } },
  { gross: 2_000_000, kwargs: {} },
  { gross: -1, kwargs: {} },
  { gross: -0.01, kwargs: {} },
].map(({ gross, kwargs }) => ({ args: [gross], kwargs, ...run(() => tax.netSalary({ gross, ...jsOptions(kwargs) })) }))

const grossForNetCases = [
  ...[0, -5, 1, 100, 5000, 7010, 10000, 15000, 50000, 400000, 600000, 5_000_000].map((net) => ({ net, kwargs: {} })),
  ...Array.from({ length: 200 }, () => ({ net: pick([between(1, 25000), between(25000, 90000), cents(1, 20000)]), kwargs: salaryOptions() })),
].map(({ net, kwargs }) => ({ args: [net], kwargs, ...run(() => tax.grossForNet(net, jsOptions(kwargs))) }))

const vatCases = [
  ...[0, 0.01, 0.05, 1, 1.005, 99.99, 100, 118, 1234.56, 1e7].flatMap((amount) =>
    ['add', 'extract'].flatMap((mode) => [18, 17, 0, 7.5].map((rate) => ({ amount, kwargs: { mode, rate } })))),
  ...Array.from({ length: 160 }, () => ({ amount: pick([cents(0, 1000), cents(0, 1e6), between(0, 50000)]), kwargs: pick([{}, { mode: 'extract' }, { rate: pick([0, 17, 18, 18.5]) }, { mode: 'extract', rate: 17 }]) })),
  { amount: -1, kwargs: {} },
].map(({ amount, kwargs }) => ({ args: [amount], kwargs, ...run(() => tax.vat(amount, jsOptions(kwargs))) }))

const purchaseEdges = [
  ...purchase.SINGLE_BRACKETS,
  ...purchase.ADDITIONAL_BRACKETS,
  ...purchase.OLEH_BRACKETS,
]
  .map((bracket) => bracket.upTo)
  .filter((value) => value !== null)

const purchaseCases = [
  ...around(purchaseEdges).flatMap((value) => ['single', 'additional', 'oleh'].map((buyer) => ({ value, buyer }))),
  ...Array.from({ length: 180 }, () => ({ value: pick([between(0, 3_000_000), between(1_000_000, 30_000_000), cents(1_900_000, 2_500_000)]), buyer: pick(['single', 'additional', 'oleh', 'other']) })),
  { value: 0, buyer: 'single' },
  { value: -3, buyer: 'single' },
].map(({ value, buyer }) => ({ args: [value, buyer], kwargs: {}, ...run(() => tax.purchaseTax(value, buyer)) }))

const selfEmployedCases = [
  ...around(monthlyEdges.map((edge) => edge * 12)).map((revenue) => ({ revenue, kwargs: { months: 12 } })),
  ...Array.from({ length: 200 }, () => {
    const kwargs = { months: pick([12, 12, 1, 3, 6, between(1, 12)]) }
    const revenue = pick([between(0, 200000), between(100000, 2_000_000), cents(0, 50000)])
    if (random() < 0.8) kwargs.expenses = pick([0, between(0, revenue), between(0, 2 * revenue + 1)])
    const points = pick([undefined, 0, 2.25, 3.5, 6.75])
    if (points !== undefined) kwargs.credit_points = points
    if (random() < 0.5) kwargs.gender = pick(['man', 'woman'])
    return { revenue, kwargs }
  }),
  { revenue: 300000, kwargs: { expenses: 60000 } },
  { revenue: 10000, kwargs: { expenses: 20000 } },
  { revenue: -1, kwargs: {} },
  { revenue: 1000, kwargs: { expenses: -1 } },
].map(({ revenue, kwargs }) => ({ args: [revenue], kwargs, ...run(() => tax.selfEmployedTax({ revenue, ...jsOptions(kwargs) })) }))

const isoOf = (year, month, date) => `${year}-${String(month).padStart(2, '0')}-${String(date).padStart(2, '0')}`
const randomIso = (low, high) => isoOf(between(low, high), between(1, 12), between(1, 28))
const addDays = (iso, days) => new Date(Date.parse(`${iso}T00:00:00Z`) + days * 86400000).toISOString().slice(0, 10)

const severanceCases = [
  ...Array.from({ length: 280 }, () => {
    const start = pick([randomIso(1990, 2025), isoOf(between(2000, 2025), pick([1, 3, 5, 8, 10, 12]), pick([29, 30, 31])), randomIso(1950, 2099)])
    const end = pick([addDays(start, between(0, 400)), addDays(start, between(300, 12000)), randomIso(2024, 2026), addDays(start, -between(1, 30))])
    const salaryValue = pick([between(1, 60000), cents(1000, 30000), `${between(1, 99)},${String(between(0, 999)).padStart(3, '0')}`, `₪ ${between(5000, 20000)}.5`, 1000000, 1000001])
    return { start, end, salary: salaryValue, kwargs: { section14: pick(['none', 'none', 'full', 'partial']) } }
  }),
  ...['2026-01-31', '2026-02-28', '2026-03-31', '2025-12-31'].flatMap((end) =>
    ['2025-01-31', '2025-02-28', '2024-02-29', '2021-03-31', '2020-01-01'].map((start) => ({ start, end, salary: 12000, kwargs: {} }))),
  { start: '2020-01-01', end: '2025-12-31', salary: 12000, kwargs: {} },
  { start: 'nope', end: '2026-01-01', salary: 1, kwargs: {} },
  { start: '2026-02-30', end: '2026-03-01', salary: 1, kwargs: {} },
  { start: '1949-12-31', end: '2026-01-01', salary: 1, kwargs: {} },
  { start: ' 2020-01-01 ', end: '2026-01-01', salary: 1, kwargs: {} },
  { start: '2020-01-01', end: '2026-01-01', salary: 0, kwargs: {} },
  { start: '2020-01-01', end: '2026-01-01', salary: 'abc', kwargs: {} },
  { start: '2020-01-01', end: '2026-01-01', salary: 1.234, kwargs: {} },
  { start: '', end: '2026-01-01', salary: 5000, kwargs: {} },
].map(({ start, end, salary: salaryValue, kwargs }) => ({
  args: [start, end, salaryValue],
  kwargs,
  ...run(() => tax.severancePay({ start, end, salary: salaryValue, ...jsOptions(kwargs) })),
}))

const creditCases = [
  { kwargs: {} },
  { kwargs: { gender: 'woman' } },
  { kwargs: { gender: 'woman', children: { six_seventeen: 2 } } },
  ...Array.from({ length: 220 }, () => {
    const kwargs = { gender: pick(['man', 'woman']) }
    if (random() < 0.7) {
      kwargs.children = Object.fromEntries(
        credits.CHILD_BANDS.filter(() => random() < 0.4).map((band) => [snake(band), between(0, 4)]),
      )
    }
    if (random() < 0.4) kwargs.degree = pick(['none', 'first', 'second'])
    if (random() < 0.4) kwargs.oleh = { month: between(1, 12), year: between(2019, 2026) }
    if (random() < 0.4) kwargs.soldier = { discharge: { month: between(1, 12), year: between(2022, 2026) }, full_service: pick([true, false]) }
    return { kwargs }
  }),
].map(({ kwargs }) => {
  const options = jsOptions(kwargs)
  if (options.children) options.children = jsOptions(options.children)
  if (options.soldier) options.soldier = jsOptions(options.soldier)
  return { args: [], kwargs, ...run(() => tax.creditPoints(options)) }
})

const recuperationCases = [
  ...Array.from({ length: 25 }, (_, index) => ({ args: [index + 1], kwargs: {} })),
  ...Array.from({ length: 260 }, () => {
    const kwargs = {}
    if (random() < 0.6) kwargs.months = pick([12, between(1, 12), 0, 13, 12.5])
    if (random() < 0.6) kwargs.job_percent = pick([100, 50, between(1, 100), 33.33, 0, 150, 12.345])
    if (random() < 0.4) kwargs.day_rate = pick([451.5, 418, 400, cents(100, 600), 0])
    return { args: [between(1, 22)], kwargs }
  }),
].map(({ args, kwargs }) => ({ args, kwargs, ...run(() => tax.recuperationPay({ seniorityYear: args[0], ...jsOptions(kwargs) })) }))

const minimumCases = ['adult', 'age17', 'age16', 'under16', 'apprentice', 'other'].flatMap((age) =>
  ['2026', '2025', '2020'].map((period) => ({ args: [], kwargs: { age, period }, ...run(() => tax.minimumWage({ age, period })) })),
)
minimumCases.push({ args: [], kwargs: {}, ...run(() => tax.minimumWage()) })

const fixtures = {
  net_salary: netSalaryCases,
  gross_for_net: grossForNetCases,
  vat: vatCases,
  purchase_tax: purchaseCases,
  self_employed_tax: selfEmployedCases,
  severance_pay: severanceCases,
  credit_points: creditCases,
  recuperation_pay: recuperationCases,
  minimum_wage: minimumCases,
}

writeFileSync(fixturesPath, `${JSON.stringify(fixtures)}\n`)
console.log(JSON.stringify(Object.fromEntries(Object.entries(fixtures).map(([name, cases]) => [name, cases.length]))))
