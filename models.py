import random
import numpy as np


class Lab1Model:
    def __init__(self):
        self.subtopics = {
            "Регулирование": {
                "P_m_i": [0.25, 0.05, 0.17, 0.12, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
                "t_step": [
                    [2.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
                ]
            },
            "Восстановление": {
                "P_m_i": [0.0, 0.1, 0.2, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
                "t_step": [
                    [1.0, 0.0, 10.0, 7.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 4.0, 0.0, 0.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
                ]
            }
        }
        self.subtopic_probs = [0.5, 0.5]
        self.sigma_coef = 0.1

    def step_time(self, subtopic_name, step_idx):
        st = self.subtopics[subtopic_name]["t_step"]
        if step_idx >= len(st[0]):
            return 0.0
        const_val = st[0][step_idx]
        if const_val != 0.0:
            return max(const_val, 0.0)

        mu = st[1][step_idx]
        sigma = abs(mu) * self.sigma_coef
        if sigma <= 0.0:
            return max(mu, 0.0)

        val = np.random.normal(mu, sigma)
        return max(val, 0.0)

    def simulate_route(self, route, subtopic_name, p_error_override=None):
        total_time = 0.0
        p_errors = self.subtopics[subtopic_name]["P_m_i"]

        for step in route:
            step_idx = (step - 1) % len(p_errors)
            t = self.step_time(subtopic_name, step_idx)
            total_time += t

            p_err = p_error_override if p_error_override is not None else p_errors[step_idx]
            while random.random() < p_err:
                total_time += t
        return total_time

    def simulate_lab1(self, n_samples=1000, p_error_override=None, routes_data=None):
        results = {"Регулирование": [], "Восстановление": [], "Общее": []}

        for _ in range(n_samples):
            subtopic_idx = random.choices([0, 1], weights=self.subtopic_probs)[0]
            subtopic_name = list(self.subtopics.keys())[subtopic_idx]

            current_routes = routes_data.get(subtopic_name, []) if routes_data else []
            if not current_routes:
                continue

            route = random.choice(current_routes)
            time_taken = self.simulate_route(route, subtopic_name, p_error_override)
            results[subtopic_name].append(time_taken)
            results["Общее"].append(time_taken)

        return results


class Lab2Model:
    def __init__(self, lab1_model):
        self.lab1 = lab1_model

    def run_simulation(self, lambda_requests, lambda_failures, r1_loss, r2_loss, max_iterations, routes_data, rho_1=1.0, rho_2=1.0, lr2_mode=0):
        if lambda_requests <= 0 or lambda_failures <= 0:
            raise ValueError("Интенсивности потоков λ1 и λ2 должны быть строго больше 0.")

        reg_routes = {"Регулирование": routes_data.get("Регулирование", [])}
        rest_routes = {"Восстановление": routes_data.get("Восстановление", [])}

        reg_results = self.lab1.simulate_lab1(1000, routes_data=reg_routes)
        t_reg_mean = np.mean(reg_results["Регулирование"]) if reg_results["Регулирование"] else 5.0

        rest_results = self.lab1.simulate_lab1(1000, routes_data=rest_routes)
        t_rest_mean = np.mean(rest_results["Восстановление"]) if rest_results["Восстановление"] else 10.0

        cycles = []
        sum_fail = 0.0
        sum_proc = 0.0
        sum_rec = 0.0
        total_arrived = 0
        total_processed = 0

        for i in range(max_iterations):
            t_fail = np.random.exponential(1.0 / lambda_failures)
            sum_fail += t_fail

            arrival = 0.0
            free_at = 0.0
            cycle_arrived = 0
            cycle_processed = 0
            cycle_t_proc = 0.0

            while True:
                arrival += np.random.exponential(1.0 / lambda_requests)
                if arrival >= t_fail:
                    break

                total_arrived += 1
                cycle_arrived += 1

                start = max(arrival, free_at)
                if start >= t_fail:
                    continue

                t_pr = self.lab1.simulate_route(random.choice(routes_data["Регулирование"]), "Регулирование") if routes_data.get("Регулирование") else t_reg_mean
                free_at = start + t_pr

                if free_at <= t_fail:
                    total_processed += 1
                    cycle_processed += 1
                    cycle_t_proc += t_pr
                else:
                    cycle_t_proc += max(0.0, t_fail - start)
                    break

            t_rec = self.lab1.simulate_route(random.choice(routes_data["Восстановление"]), "Восстановление") if routes_data.get("Восстановление") else t_rest_mean

            sum_proc += cycle_t_proc
            sum_rec += t_rec

            cycles.append({
                "id": i + 1,
                "arrival": cycle_arrived,
                "processed": cycle_processed,
                "t_fail": round(t_fail, 3),
                "t_proc": round(cycle_t_proc, 3),
                "t_rec": round(t_rec, 3),
                "loss": round((rho_1 * cycle_t_proc * r1_loss) + (rho_2 * t_rec * r2_loss), 2)
            })

        numerator = 0.0
        if lr2_mode != 2:
            numerator += rho_1 * sum_proc
        if lr2_mode != 1:
            numerator += rho_2 * sum_rec

        total_loss = numerator / (sum_fail + sum_rec) if (sum_fail + sum_rec) > 0 else 0.0
        return cycles, total_loss, t_reg_mean, t_rest_mean