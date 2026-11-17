import random
import numpy as np


class Lab1Model:
    def __init__(self):
        self.subtopics = {
            "Регулирование": {"step_times": [2, 5, 0, 0], "errors": [0.25, 0.05, 0.17, 0.12]},
            "Восстановление": {"step_times": [1, 0, 10, 7], "errors": [0.0, 0.1, 0.2, 0.2]}
        }
        self.subtopic_probs = [0.5, 0.5]

    def simulate_route(self, route, subtopic_name, p_error_override=None):
        total_time = 0
        step_times = self.subtopics[subtopic_name]["step_times"]
        errors = self.subtopics[subtopic_name]["errors"]

        for step in route:
            step_type = (step - 1) % len(step_times)
            base_time = step_times[step_type]
            p_err = p_error_override if p_error_override is not None else errors[step_type]

            while random.random() < p_err:
                total_time += base_time
            total_time += base_time
        return total_time

    def simulate_lab1(self, n_samples=1000, p_error_override=None, routes_data=None):
        # Возвращаем словарь с результатами отдельно по подтемам
        results = {"Регулирование": [], "Восстановление": [], "Общее": []}

        for _ in range(n_samples):
            subtopic_idx = random.choices([0, 1], weights=self.subtopic_probs)[0]
            subtopic_name = list(self.subtopics.keys())[subtopic_idx]

            if routes_data and subtopic_name in routes_data and routes_data[subtopic_name]:
                route = random.choice(routes_data[subtopic_name])
            else:
                continue

            time_taken = self.simulate_route(route, subtopic_name, p_error_override)
            results[subtopic_name].append(time_taken)
            results["Общее"].append(time_taken)

        return results


class Lab2Model:
    def __init__(self, lab1_model):
        self.lab1 = lab1_model

    def run_simulation(self, lambda_requests, lambda_failures, r1_loss, r2_loss, max_iterations, routes_data):
        # Получаем средние времена из ЛР1
        reg_results = self.lab1.simulate_lab1(1000, routes_data=routes_data)
        t_reg_mean = np.mean(reg_results["Регулирование"]) if reg_results["Регулирование"] else 5.0

        rest_routes = {"Восстановление": routes_data.get("Восстановление", [])}
        rest_results = self.lab1.simulate_lab1(1000, routes_data=rest_routes)
        t_rest_mean = np.mean(rest_results["Восстановление"]) if rest_results["Восстановление"] else 10.0

        current_time = 0.0
        time_to_next_failure = np.random.exponential(1.0 / lambda_failures)

        total_delay = 0.0
        total_downtime = 0.0
        logs = []

        for i in range(max_iterations):
            dt_req = np.random.exponential(1.0 / lambda_requests)
            arrival_time = current_time + dt_req

            if time_to_next_failure <= arrival_time:
                downtime = t_rest_mean
                total_downtime += downtime
                current_time = time_to_next_failure + downtime
                time_to_next_failure = current_time + np.random.exponential(1.0 / lambda_failures)

                logs.append({
                    "id": i + 1,
                    "arrival": round(arrival_time, 3),
                    "end": round(arrival_time, 3),
                    "status": "не выполнена",
                    "loss": round(downtime * r2_loss, 2)
                })
            else:
                processing_end_time = arrival_time + t_reg_mean

                if time_to_next_failure < processing_end_time:
                    delay = max(0, time_to_next_failure - arrival_time)
                    downtime = t_rest_mean
                    total_delay += delay
                    total_downtime += downtime

                    logs.append({
                        "id": i + 1,
                        "arrival": round(arrival_time, 3),
                        "end": round(time_to_next_failure, 3),
                        "status": "не выполнена",
                        "loss": round((delay * r1_loss) + (downtime * r2_loss), 2)
                    })
                    current_time = time_to_next_failure + downtime
                    time_to_next_failure = current_time + np.random.exponential(1.0 / lambda_failures)
                else:
                    logs.append({
                        "id": i + 1,
                        "arrival": round(arrival_time, 3),
                        "end": round(processing_time, 3) if 'processing_time' in locals() else round(
                            processing_end_time, 3),
                        "status": "выполнена",
                        "loss": round(t_reg_mean * r1_loss, 2)
                    })
                    current_time = processing_end_time

        total_loss = (total_delay * r1_loss) + (total_downtime * r2_loss)
        return logs, total_loss, t_reg_mean, t_rest_mean