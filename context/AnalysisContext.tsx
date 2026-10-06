"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface AnalysisContextType {
  country1: string;
  country2: string;
  period: string;
  focus: string[];

  setAnalysis: (
    country1: string,
    country2: string,
    period: string,
    focus: string[]
  ) => void;

  clearAnalysis: () => void;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(
  undefined
);

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [country1, setCountry1] = useState("");
  const [country2, setCountry2] = useState("");
  const [period, setPeriod] = useState("90");
  const [focus, setFocus] = useState<string[]>(["conflict"]);

  const setAnalysis = (
    newCountry1: string,
    newCountry2: string,
    newPeriod: string,
    newFocus: string[]
  ) => {
    setCountry1(newCountry1);
    setCountry2(newCountry2);
    setPeriod(newPeriod);
    setFocus(newFocus);
  };

  const clearAnalysis = () => {
    setCountry1("");
    setCountry2("");
    setPeriod("90");
    setFocus(["conflict"]);
  };

  return (
    <AnalysisContext.Provider
      value={{
        country1,
        country2,
        period,
        focus,
        setAnalysis,
        clearAnalysis,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const context = useContext(AnalysisContext);

  if (!context) {
    throw new Error(
      "useAnalysis must be used inside AnalysisProvider"
    );
  }

  return context;
}